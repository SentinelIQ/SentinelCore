import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from companies.models import Company
from dashboard.models import DashboardPreference

User = get_user_model()


class DashboardPreferenceTests(APITestCase):
    """
    Test cases for the dashboard preferences endpoint.
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
        
        # URL for preferences endpoint
        self.url = reverse('dashboard:preferences')
        
        # Authenticate the user
        self.client.force_authenticate(user=self.user)
    
    def test_get_dashboard_preferences(self):
        """Test getting dashboard preferences."""
        # Make the request
        response = self.client.get(self.url)
        
        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that preferences were created for the user
        self.assertTrue(DashboardPreference.objects.filter(user=self.user).exists())
        
        # Check response structure
        data = response.data.get('data', {})
        self.assertIn('layout', data)
        self.assertIn('widget_preferences', data)
        self.assertIn('default_time_range', data)
        
    def test_update_dashboard_preferences(self):
        """Test updating dashboard preferences."""
        # Prepare update data
        update_data = {
            'default_time_range': 14,
            'layout': {'layout_type': 'grid', 'columns': 3},
            'widget_preferences': {
                'alerts_widget': {'enabled': True, 'position': 1},
                'incidents_widget': {'enabled': True, 'position': 2}
            }
        }
        
        # Make the request
        response = self.client.put(
            self.url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify data was updated
        pref = DashboardPreference.objects.get(user=self.user)
        self.assertEqual(pref.default_time_range, 14)
        self.assertEqual(pref.layout, update_data['layout'])
        self.assertEqual(pref.widget_preferences, update_data['widget_preferences'])
        
    def test_invalid_update_data(self):
        """Test updating with invalid data."""
        # Prepare invalid update data
        invalid_data = {
            'default_time_range': 'not-an-integer'
        }
        
        # Make the request
        response = self.client.put(
            self.url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied."""
        # Logout
        self.client.force_authenticate(user=None)
        
        # Make the request
        response = self.client.get(self.url)
        
        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 