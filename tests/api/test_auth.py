from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()


class AuthAPITestCase(APITestCase):
    """
    Test case for authentication API endpoints.
    """
    def setUp(self):
        # Create a company
        self.company = Company.objects.create(name="Test Company")
        
        # Create users
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="password123"
        )
        
        self.admin_company = User.objects.create_user(
            username="company_admin",
            email="admin@company.com",
            password="password123",
            role=User.Role.ADMIN_COMPANY,
            company=self.company
        )
        
        self.analyst_company = User.objects.create_user(
            username="company_analyst",
            email="analyst@company.com",
            password="password123",
            role=User.Role.ANALYST_COMPANY,
            company=self.company
        )
        
        # Set up URLs for v1 API
        self.token_url = reverse('v1:auth:token_obtain_pair')
        self.token_refresh_url = reverse('v1:auth:token_refresh')
    
    def test_user_login(self):
        """Test that users can log in and get a JWT token."""
        # Superuser login
        response = self.client.post(
            self.token_url,
            {'username': 'admin', 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Company admin login
        response = self.client.post(
            self.token_url,
            {'username': 'company_admin', 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Company analyst login
        response = self.client.post(
            self.token_url,
            {'username': 'company_analyst', 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_invalid_login(self):
        """Test that invalid credentials don't work."""
        response = self.client.post(
            self.token_url,
            {'username': 'admin', 'password': 'wrong_password'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Test that refresh tokens can be used to get new access tokens."""
        # Get initial token
        response = self.client.post(
            self.token_url,
            {'username': 'admin', 'password': 'password123'},
            format='json'
        )
        refresh_token = response.data['refresh']
        
        # Use refresh token to get new access token
        response = self.client.post(
            self.token_refresh_url,
            {'refresh': refresh_token},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data) 