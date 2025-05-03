from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from auth_app.models import User
from companies.models import Company
from api.v1.auth.enums import UserRoleEnum


class CompanyCreateTests(TestCase):
    """
    Tests for company creation
    """
    def setUp(self):
        self.client = APIClient()
        # Create a superuser for testing
        self.superuser = User.objects.create_superuser(
            username='admin_test',
            email='admin@example.com',
            password='securepass123'
        )
        # Create a company admin user
        self.company = Company.objects.create(name='Test Company')
        self.admin_user = User.objects.create_user(
            username='company_admin',
            email='admin@company.com',
            password='securepass123',
            role=UserRoleEnum.ADMIN_COMPANY.value,
            company=self.company
        )
    
    def test_create_company_as_superuser(self):
        """
        Verify if a superuser can create a company
        """
        # Login as superuser
        self.client.force_authenticate(user=self.superuser)
        
        # Data for new company, including admin user data
        data = {
            'name': 'New Test Company',
            'admin_user': {
                'username': 'new_company_admin',
                'email': 'admin@newcompany.com',
                'password': 'securepass456',
                'first_name': 'Admin',
                'last_name': 'New Company'
            }
        }
        
        # Make the request
        response = self.client.post(
            reverse('company-list'),
            data,
            format='json'
        )
        
        # Verify if the company was created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Company.objects.count(), 2)
        self.assertEqual(Company.objects.get(name='New Test Company').name, 'New Test Company')
        
        # Verify if the admin user was created
        self.assertTrue(User.objects.filter(username='new_company_admin').exists())
        admin_user = User.objects.get(username='new_company_admin')
        self.assertEqual(admin_user.email, 'admin@newcompany.com')
        self.assertEqual(admin_user.role, UserRoleEnum.ADMIN_COMPANY.value)
        self.assertEqual(admin_user.company.name, 'New Test Company')
    
    def test_create_company_as_admin_forbidden(self):
        """
        Verify if a company admin cannot create other companies
        """
        # Login as company admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Data for new company
        data = {
            'name': 'Another Company',
            'admin_username': 'another_admin',
            'admin_email': 'admin@anothercompany.com',
            'admin_password': 'securepass789'
        }
        
        # Make the request
        response = self.client.post(
            reverse('company-list'),
            data,
            format='json'
        )
        
        # Verify that creation was denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Company.objects.count(), 1) 