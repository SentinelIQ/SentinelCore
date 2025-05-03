from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from auth_app.models import User
from companies.models import Company
from rest_framework_simplejwt.tokens import RefreshToken


class UserAuthenticationTests(TestCase):
    """
    Tests for user authentication functionality
    """
    def setUp(self):
        self.client = APIClient()
        # Create a company for testing
        self.company = Company.objects.create(name='Test Company')
        
        # Create a regular user for testing
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123',
            role=User.Role.ANALYST_COMPANY,
            company=self.company
        )
        
        # Create a superuser for testing
        self.superuser = User.objects.create_superuser(
            username='admin_test',
            email='admin@example.com',
            password='securepass123'
        )
        
        # Auth URLs
        self.token_url = reverse('token-obtain')
        self.email_token_url = reverse('token-email')
        self.token_refresh_url = reverse('token-refresh')
    
    def test_user_can_obtain_token_with_username(self):
        """
        Verify a user can obtain an access token using username/password
        """
        data = {
            'username': 'testuser',
            'password': 'securepass123'
        }
        
        response = self.client.post(self.token_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check the response format
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['code'], 200)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertIn('user', response.data['data'])
    
    def test_user_can_obtain_token_with_email(self):
        """
        Verify a user can obtain an access token using email/password
        """
        data = {
            'email': 'test@example.com',
            'password': 'securepass123'
        }
        
        response = self.client.post(self.email_token_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['code'], 200)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertIn('user', response.data['data'])
        # Verify the user data is correct
        self.assertEqual(response.data['data']['user']['username'], 'testuser')
        self.assertEqual(response.data['data']['user']['email'], 'test@example.com')
    
    def test_superuser_can_obtain_token_with_email(self):
        """
        Verify a superuser can obtain an access token using email/password
        """
        data = {
            'email': 'admin@example.com',
            'password': 'securepass123'
        }
        
        response = self.client.post(self.email_token_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['user']['is_superuser'], True)
    
    def test_invalid_login_credentials_username(self):
        """
        Verify invalid username credentials are rejected
        """
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.token_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 'error')
    
    def test_invalid_login_credentials_email(self):
        """
        Verify invalid email credentials are rejected
        """
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.email_token_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 'error')
    
    def test_invalid_refresh_token(self):
        """
        Verify an invalid refresh token is rejected
        """
        data = {
            'refresh': 'invalid-token'
        }
        
        response = self.client.post(self.token_refresh_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 'error') 