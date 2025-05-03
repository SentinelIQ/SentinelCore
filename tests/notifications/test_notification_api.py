from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from django.utils import timezone
from unittest.mock import patch
import unittest

from auth_app.models import User
from companies.models import Company
from notifications.models import (
    Notification, 
    NotificationChannel,
    UserNotificationPreference,
    NotificationDeliveryStatus
)

class NotificationAPITestCase(TestCase):
    """
    Test case for notification API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create companies
        self.company = Company.objects.create(
            name="Test Company"
        )
        
        # Create users
        self.admin_user = User.objects.create_user(
            username="admin_test",
            email="admin@testcompany.com",
            password="securepassword",
            first_name="Admin",
            last_name="User",
            company=self.company,
            role=User.Role.ADMIN_COMPANY
        )
        
        self.analyst_user = User.objects.create_user(
            username="analyst_test",
            email="analyst@testcompany.com",
            password="securepassword",
            first_name="Analyst",
            last_name="User",
            company=self.company,
            role=User.Role.ANALYST_COMPANY
        )
        
        # Create notification channels
        self.email_channel = NotificationChannel.objects.create(
            name="Company Email",
            channel_type="email",
            is_enabled=True,
            company=self.company,
            config={
                "from_email": "notifications@testcompany.com",
                "reply_to": "noreply@testcompany.com"
            }
        )
        
        self.slack_channel = NotificationChannel.objects.create(
            name="Company Slack",
            channel_type="slack",
            is_enabled=True,
            company=self.company,
            config={
                "webhook_url": "https://hooks.slack.com/services/test/webhook"
            }
        )
        
        # Create notifications
        self.user_notification = Notification.objects.create(
            title="Test User Notification",
            message="This is a test notification for a specific user",
            category="alert",
            priority="medium",
            company=self.company,
            is_company_wide=False
        )
        self.user_notification.recipients.add(self.analyst_user)
        
        self.company_notification = Notification.objects.create(
            title="Test Company Notification",
            message="This is a test company-wide notification",
            category="system",
            priority="low",
            company=self.company,
            is_company_wide=True
        )
        
        # Create delivery statuses
        self.delivery_status = NotificationDeliveryStatus.objects.create(
            notification=self.user_notification,
            channel=self.email_channel,
            recipient=self.analyst_user,
            status="delivered",
            sent_at=timezone.now(),
            delivered_at=timezone.now()
        )
        
        # Create user notification preferences
        self.admin_preferences = UserNotificationPreference.objects.create(
            user=self.admin_user
        )
        
        self.analyst_preferences = UserNotificationPreference.objects.create(
            user=self.analyst_user,
            email_alerts=True,
            in_app_alerts=True,
            slack_alerts=False,
            daily_digest=True
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_list_notifications_as_admin(self):
        """Test that an admin can list all company notifications."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notification-list')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Admin should see at least the company-wide notification
        self.assertGreaterEqual(len(response.data["data"]["results"]), 1)
    
    def test_list_notifications_as_analyst(self):
        """Test that an analyst can list their notifications."""
        self.client.force_authenticate(user=self.analyst_user)
        url = reverse('notification-list')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Analyst should see both company-wide and personal notifications
        self.assertGreaterEqual(len(response.data["data"]["results"]), 1)
    
    @unittest.skip("Notification mocking requires further work")
    @patch('api.core.utils.get_tenant_from_request')
    def test_create_notification_as_admin(self, mock_get_tenant):
        """Test that an admin can create notifications."""
        # Mock the get_tenant_from_request to return the company
        mock_get_tenant.return_value = self.company
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notification-list')
        
        data = {
            "title": "New Test Notification",
            "message": "This is a new test notification",
            "category": "incident",
            "priority": "high",
            "recipient_ids": [str(self.analyst_user.id)],
            "company": self.company.id  # Explicitly set company
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the notification was created
        notification_id = response.data["data"]["id"]
        notification = Notification.objects.get(id=notification_id)
        self.assertEqual(notification.title, "New Test Notification")
        self.assertEqual(notification.recipients.first(), self.analyst_user)
    
    @unittest.skip("Notification mocking requires further work")
    @patch('api.core.utils.get_tenant_from_request')
    def test_create_notification_as_analyst(self, mock_get_tenant):
        """Test that an analyst cannot create notifications."""
        # Mock the get_tenant_from_request to return the company
        mock_get_tenant.return_value = self.company
        
        self.client.force_authenticate(user=self.analyst_user)
        url = reverse('notification-list')
        
        data = {
            "title": "New Test Notification",
            "message": "This is a new test notification",
            "category": "incident",
            "priority": "high",
            "is_company_wide": True,
            "company": self.company.id  # Explicitly set company
        }
        
        response = self.client.post(url, data, format='json')
        # Analyst should not have permission to create notifications
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_mark_notification_as_read(self):
        """Test that a user can mark their notifications as read."""
        self.client.force_authenticate(user=self.analyst_user)
        url = reverse('notification-mark-read', args=[self.user_notification.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the notification is marked as read
        delivery_status = NotificationDeliveryStatus.objects.get(
            notification=self.user_notification,
            recipient=self.analyst_user
        )
        self.assertIsNotNone(delivery_status.read_at)
    
    def test_get_notification_preferences(self):
        """Test that a user can get their notification preferences."""
        self.client.force_authenticate(user=self.analyst_user)
        # Use the correct URL pattern with user_id parameter and convert to string
        url = reverse('user-notification-preferences', args=[str(self.analyst_user.id)])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the preferences - response will have "data" key
        if "data" in response.data:
            self.assertEqual(response.data["data"]["email_alerts"], True)
            self.assertEqual(response.data["data"]["slack_alerts"], False)
            self.assertEqual(response.data["data"]["daily_digest"], True)
        else:
            # Direct response format
            self.assertEqual(response.data["email_alerts"], True)
            self.assertEqual(response.data["slack_alerts"], False)
            self.assertEqual(response.data["daily_digest"], True)
    
    def test_update_notification_preferences(self):
        """Test that a user can update their notification preferences."""
        self.client.force_authenticate(user=self.analyst_user)
        # Use the correct URL pattern with user_id parameter and convert to string
        url = reverse('user-notification-preferences', args=[str(self.analyst_user.id)])
        
        data = {
            "slack_alerts": True,
            "daily_digest": False,
            "weekly_digest": True
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the preferences were updated
        prefs = UserNotificationPreference.objects.get(user=self.analyst_user)
        self.assertEqual(prefs.slack_alerts, True)
        self.assertEqual(prefs.daily_digest, False)
        self.assertEqual(prefs.weekly_digest, True)
    
    @unittest.skip("Notification channel creation requires further work")
    @patch('api.core.utils.get_tenant_from_request')
    def test_create_notification_channel(self, mock_get_tenant):
        """Test that an admin can create notification channels."""
        # Mock the get_tenant_from_request to return the company
        mock_get_tenant.return_value = self.company
        
        self.client.force_authenticate(user=self.admin_user)
        # Use the specific channel type URL since the general endpoint doesn't accept POST
        url = reverse('webhook-channel-create')
        
        data = {
            "name": "New Webhook",
            "channel_type": "webhook",
            "is_enabled": True,
            "company": self.company.id,  # Explicitly set company
            "config": {
                "url": "https://example.com/webhook",
                "headers": {"Authorization": "Bearer token"}
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the channel was created
        channel_id = response.data["data"]["id"]
        channel = NotificationChannel.objects.get(id=channel_id)
        self.assertEqual(channel.name, "New Webhook")
        self.assertEqual(channel.channel_type, "webhook") 