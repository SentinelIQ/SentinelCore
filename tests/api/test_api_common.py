from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from auth_app.models import User
from companies.models import Company
from api.v1.auth.enums import UserRoleEnum


class CommonAPITests(TestCase):
    """
    Tests for common API endpoints (health check, whoami, etc)
    """
    def setUp(self):
        self.client = APIClient()
        
        # Create a company for testing
        self.company = Company.objects.create(name='Test Company')
        
        # Create a user for testing
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepassword123',
            role=UserRoleEnum.ADMIN_COMPANY.value,
            company=self.company
        )
        
        # URLs - using literal paths instead of reverse
        self.health_check_url = '/api/v1/common/health-check/'  # Updated path based on logs
        self.whoami_url = '/api/v1/common/whoami/'  # Updated path based on logs
    
    def test_health_check_endpoint(self):
        """
        Verify if the health check endpoint returns 200
        """
        response = self.client.get(self.health_check_url)
        
        print(f"Health check response: {response.status_code}")
        print(f"Health check content: {response.content}")
        
        # Health check should return status 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify if the response contains the 'status' key
        self.assertIn('status', response.json())
    
    def test_whoami_endpoint_unauthenticated(self):
        """
        Verify if the whoami endpoint returns 401 for unauthenticated users
        """
        response = self.client.get(self.whoami_url)
        
        print(f"Whoami unauthenticated response: {response.status_code}")
        print(f"Whoami unauthenticated content: {response.content}")
        
        # Without authentication, it should return 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_whoami_endpoint_authenticated(self):
        """
        Verify if the whoami endpoint returns the authenticated user's data
        """
        # Authenticate the user
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.whoami_url)
        
        print(f"Whoami authenticated response: {response.status_code}")
        print(f"Whoami authenticated content: {response.content}")
        
        # With authentication, it should return 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify if user data is in the response
        self.assertIn('data', response.json())
        data = response.json()['data']
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testuser') 