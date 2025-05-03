from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from auth_app.models import User
from companies.models import Company


class CompanyCustomActionsTests(TestCase):
    """
    Tests for Company custom actions
    """
    def setUp(self):
        self.client = APIClient()
        
        # Create test company
        self.company = Company.objects.create(name='Test Company')
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin_test_actions',
            email='admin_test_actions@sentineliq.com',
            password='securepass123'
        )
        
        # Create company admin
        self.company_admin = User.objects.create_user(
            username='admin_company1_actions',
            email='admin_company1_actions@company.com',
            password='securepass123',
            role=User.Role.ADMIN_COMPANY,
            company=self.company
        )
        
        # Create two regular users in the company
        self.user1 = User.objects.create_user(
            username='user1_company1_actions',
            email='user1_company1_actions@company.com',
            password='securepass123',
            role=User.Role.ANALYST_COMPANY,
            company=self.company
        )
        
        self.user2 = User.objects.create_user(
            username='user2_company1_actions',
            email='user2_company1_actions@company.com',
            password='securepass123',
            role=User.Role.ANALYST_COMPANY,
            company=self.company
        )
        
        # URLs for company actions
        self.company_stats_url = reverse('company-statistics', kwargs={'pk': self.company.id})
        self.company_user_stats_url = reverse('company-user-stats', kwargs={'pk': self.company.id})
        self.company_deactivate_users_url = reverse('company-deactivate-users', kwargs={'pk': self.company.id})
    
    def test_superuser_can_view_user_stats(self):
        """
        Verify a superuser can view user statistics for a company
        """
        self.client.force_authenticate(user=self.superuser)
        
        response = self.client.get(self.company_user_stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the right data
        self.assertEqual(response.data['status'], 'success')
        
        # Check that the company ID in the response is correct
        self.assertEqual(response.data['data']['company']['id'], self.company.id)
        
        # Check that the stats include all three users
        self.assertEqual(response.data['data']['stats']['total'], 3)
    
    def test_company_admin_can_view_user_stats(self):
        """
        Verify a company admin can view user statistics for their own company
        """
        self.client.force_authenticate(user=self.company_admin)
        
        response = self.client.get(self.company_user_stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the right data
        self.assertEqual(response.data['status'], 'success')
        
        # Check that the company ID in the response is correct
        self.assertEqual(response.data['data']['company']['id'], self.company.id)
        
        # Check that the stats include all three users
        self.assertEqual(response.data['data']['stats']['total'], 3)
    
    def test_regular_user_cannot_view_user_stats(self):
        """
        Verify a regular user cannot view user statistics
        """
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(self.company_user_stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_superuser_can_deactivate_users(self):
        """
        Verify a superuser can deactivate users in a company
        """
        self.client.force_authenticate(user=self.superuser)
        
        # Ensure all users are active initially
        self.assertTrue(User.objects.get(id=self.user1.id).is_active)
        self.assertTrue(User.objects.get(id=self.user2.id).is_active)
        
        data = {
            'user_ids': [self.user1.id, self.user2.id]
        }
        
        response = self.client.post(self.company_deactivate_users_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response format
        self.assertEqual(response.data['status'], 'success')
        
        # Check that the correct number of users were deactivated
        self.assertEqual(response.data['data']['deactivated_count'], 2)
        
        # Verify users were actually deactivated in the database
        self.assertFalse(User.objects.get(id=self.user1.id).is_active)
        self.assertFalse(User.objects.get(id=self.user2.id).is_active)
    
    def test_company_admin_can_deactivate_users(self):
        """
        Verify a company admin can deactivate users in their own company
        """
        self.client.force_authenticate(user=self.company_admin)
        
        # Ensure users are active initially
        self.assertTrue(User.objects.get(id=self.user1.id).is_active)
        
        data = {
            'user_ids': [self.user1.id]
        }
        
        response = self.client.post(self.company_deactivate_users_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response format
        self.assertEqual(response.data['status'], 'success')
        
        # Check that the correct number of users were deactivated
        self.assertEqual(response.data['data']['deactivated_count'], 1)
        
        # Verify users were actually deactivated in the database
        self.assertFalse(User.objects.get(id=self.user1.id).is_active)
    
    def test_regular_user_cannot_deactivate_users(self):
        """
        Verify a regular user cannot deactivate other users
        """
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'user_ids': [self.user2.id]
        }
        
        response = self.client.post(self.company_deactivate_users_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify the target user is still active
        self.assertTrue(User.objects.get(id=self.user2.id).is_active)
    
    def test_company_admin_cannot_deactivate_another_admin(self):
        """
        Verify a company admin cannot deactivate another admin (only superuser can)
        """
        self.client.force_authenticate(user=self.company_admin)
        
        # Create another admin for the company
        another_admin = User.objects.create_user(
            username='another_admin',
            email='another_admin@company.com',
            password='securepass123',
            role=User.Role.ADMIN_COMPANY,
            company=self.company
        )
        
        data = {
            'user_ids': [another_admin.id]
        }
        
        response = self.client.post(self.company_deactivate_users_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that no users were deactivated
        self.assertEqual(response.data['data']['deactivated_count'], 0)
        
        # Verify the admin is still active
        self.assertTrue(User.objects.get(id=another_admin.id).is_active) 