import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from companies.models import Company
from dashboard.models import DashboardPreference

User = get_user_model()


class DashboardSummaryTests(APITestCase):
    """
    Test cases for the dashboard summary endpoint.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company"
        )
        
        # Create a user with dashboard permissions
        self.user = User.objects.create_user(
            username="testuser",
            email="test@testcompany.com",
            password="testpassword123",
            company=self.company,
            role="admin_company"  # Role with dashboard permissions
        )
        
        # URL for summary endpoint
        self.url = reverse('dashboard:summary')
        
        # Authenticate the user
        self.client.force_authenticate(user=self.user)
    
    def test_get_dashboard_summary(self):
        """Test getting dashboard summary."""
        # Make the request
        response = self.client.get(self.url)
        
        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        data = response.data.get('data', {})
        self.assertIn('timeframe', data)
        self.assertIn('alerts', data)
        self.assertIn('incidents', data)
        self.assertIn('tasks', data)
        
        # Check timeframe data
        self.assertIn('start_date', data['timeframe'])
        self.assertIn('end_date', data['timeframe'])
        self.assertIn('days', data['timeframe'])
        
    def test_get_dashboard_summary_with_days_param(self):
        """Test getting dashboard summary with custom days parameter."""
        # Make the request with days parameter
        response = self.client.get(f"{self.url}?days=7")
        
        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check timeframe data
        data = response.data.get('data', {})
        self.assertEqual(data['timeframe']['days'], 7)
        
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied."""
        # Logout
        self.client.force_authenticate(user=None)
        
        # Make the request
        response = self.client.get(self.url)
        
        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_unauthorized_role_access(self):
        """Test access without proper role permissions."""
        # Create a user with insufficient permissions
        restricted_user = User.objects.create_user(
            username="restricted",
            email="restricted@testcompany.com",
            password="restricted123",
            company=self.company,
            role="custom_role"  # Role without dashboard permissions
        )
        
        # Authenticate with the restricted user
        self.client.force_authenticate(user=restricted_user)
        
        # Make the request
        response = self.client.get(self.url)
        
        # Check response status code - should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 