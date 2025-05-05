"""
Tests for the audit logs API.
"""

import json
from django.urls import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from alerts.models import Alert
from companies.models import Company
from api.v1.audit_logs.serializers import AuditLogSerializer
from api.v1.auth.utils import get_tokens_for_user

User = get_user_model()


@override_settings(MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.core.middleware.audit_middleware.EnhancedAuditlogMiddleware',
])
class AuditLogsAPITests(TestCase):
    """
    Tests for audit logs API.
    
    Verifies if the endpoints are working correctly
    and if the logs are properly recorded.
    """
    
    def setUp(self):
        """
        Initial setup for tests.
        
        - Creates admin and normal users
        - Creates companies for users
        - Sets up API client
        - Creates some audit logs
        """
        # Create company
        self.company = Company.objects.create(
            name="Test Company",
            domain="testcompany.com",
            is_active=True
        )
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        
        # Create normal user
        self.normal_user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="userpass123",
            company=self.company
        )
        
        # Setup API client
        self.client = APIClient()
        
        # Authenticate the admin for tests
        tokens = get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        
        # Create some audit logs for testing
        # 1. Create an alert
        self.alert = Alert.objects.create(
            title="Test Alert",
            description="Test Description",
            severity="high",
            status="new",
            company=self.company
        )
        
        # 2. Create logs for the alert
        self.content_type = ContentType.objects.get_for_model(Alert)
        
        # Creation log
        self.create_log = LogEntry.objects.create(
            content_type=self.content_type,
            object_pk=str(self.alert.pk),
            object_repr=str(self.alert),
            action=LogEntry.Action.CREATE,
            actor=self.admin_user,
            additional_data={
                'entity_type': 'alert',
                'company_id': str(self.company.id),
                'company_name': self.company.name,
            }
        )
        
        # Update log
        self.update_log = LogEntry.objects.create(
            content_type=self.content_type,
            object_pk=str(self.alert.pk),
            object_repr=str(self.alert),
            action=LogEntry.Action.UPDATE,
            actor=self.normal_user,
            additional_data={
                'entity_type': 'alert',
                'company_id': str(self.company.id),
                'company_name': self.company.name,
                'changed_fields': ['status'],
                'old_status': 'new',
                'new_status': 'in_progress',
            }
        )
        
    def test_list_logs(self):
        """Tests if log listing works correctly."""
        url = reverse('audit-log-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)
        self.assertTrue('count' in response.data)
        self.assertTrue(response.data['count'] >= 2)  # At least the logs we created
    
    def test_filter_by_entity_type(self):
        """Tests if filtering by entity type works."""
        url = reverse('audit-log-list')
        response = self.client.get(url, {'entity_type': 'alert'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data['results']:
            self.assertEqual(log['entity_type'], 'alert')
            
    def test_filter_by_action(self):
        """Tests if filtering by action works."""
        url = reverse('audit-log-list')
        response = self.client.get(url, {'action': LogEntry.Action.UPDATE})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data['results']:
            self.assertEqual(log['action_display'], 'Update')
            
    def test_filter_by_user(self):
        """Tests if filtering by user works."""
        url = reverse('audit-log-list')
        response = self.client.get(url, {'username': self.normal_user.username})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data['results']:
            self.assertEqual(log['user_display'], self.normal_user.username)
            
    def test_detail_view(self):
        """Tests if detailed log view works."""
        url = reverse('audit-log-detail', args=[self.create_log.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], str(self.create_log.id))
        self.assertEqual(response.data['data']['entity_type'], 'alert')
        
    def test_export_csv(self):
        """Tests if CSV export works."""
        url = reverse('audit-log-export')
        response = self.client.get(url, {'format': 'csv'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue('attachment; filename=' in response['Content-Disposition'])
        
    def test_export_json(self):
        """Tests if JSON export works."""
        url = reverse('audit-log-export')
        response = self.client.get(url, {'format': 'json'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTrue('attachment; filename=' in response['Content-Disposition'])
        
        # Verify if content is valid JSON
        try:
            data = json.loads(response.content)
            self.assertTrue(isinstance(data, list))
            self.assertTrue(len(data) >= 2)  # At least the logs we created
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")
            
    def test_permissions(self):
        """Tests if permissions are working correctly."""
        # Switch to normal user
        self.client.credentials()
        tokens = get_tokens_for_user(self.normal_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        
        # Normal user should only see logs from their company
        url = reverse('audit-log-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data['results']:
            # Verify if log belongs to user's company
            self.assertEqual(log.get('company_id', None), str(self.company.id))
            
    def test_company_filtering(self):
        """Tests if filtering by company works."""
        url = reverse('audit-log-list')
        response = self.client.get(url, {'company_id': str(self.company.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data['results']:
            # Verify if log belongs to specified company
            self.assertEqual(log.get('company_id', None), str(self.company.id))
            
    def test_date_filtering(self):
        """Tests if date filtering works."""
        import datetime
        from django.utils import timezone
        
        # Use today's period
        url = reverse('audit-log-list')
        response = self.client.get(url, {'period': 'today'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if logs are from today
        today = timezone.now().date()
        for log in response.data['results']:
            log_date = datetime.datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).date()
            self.assertEqual(log_date, today)


@override_settings(MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.core.middleware.audit_middleware.EnhancedAuditlogMiddleware',
])
class AuditLogReportAPITests(TestCase):
    """
    Tests for audit log reports API.
    
    Verifies if the endpoints of the report are working correctly
    and returning the expected metrics.
    """
    
    def setUp(self):
        """
        Initial setup for tests.
        
        - Creates users and companies
        - Sets up API client
        - Creates audit logs for testing
        """
        # Create company
        self.company = Company.objects.create(
            name="Test Company",
            domain="testcompany.com",
            is_active=True
        )
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        
        # Create normal user
        self.normal_user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="userpass123",
            company=self.company
        )
        
        # Setup API client
        self.client = APIClient()
        
        # Authenticate the admin for tests
        tokens = get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        
        # Create alert and incident for logs
        self.alert = Alert.objects.create(
            title="Test Alert",
            description="Test Description",
            severity="high",
            status="new",
            company=self.company
        )
        
        # Create content types
        self.alert_content_type = ContentType.objects.get_for_model(Alert)
        self.user_content_type = ContentType.objects.get_for_model(User)
        
        # Create logs of different types
        # 1. Creation of alert
        LogEntry.objects.create(
            content_type=self.alert_content_type,
            object_pk=str(self.alert.pk),
            object_repr=str(self.alert),
            action=LogEntry.Action.CREATE,
            actor=self.admin_user,
            additional_data={
                'entity_type': 'alert',
                'company_id': str(self.company.id),
                'company_name': self.company.name,
            }
        )
        
        # 2. Update of alert
        LogEntry.objects.create(
            content_type=self.alert_content_type,
            object_pk=str(self.alert.pk),
            object_repr=str(self.alert),
            action=LogEntry.Action.UPDATE,
            actor=self.normal_user,
            additional_data={
                'entity_type': 'alert',
                'company_id': str(self.company.id),
                'company_name': self.company.name,
            }
        )
        
        # 3. User login
        LogEntry.objects.create(
            content_type=self.user_content_type,
            object_pk=str(self.normal_user.pk),
            object_repr=str(self.normal_user),
            action=LogEntry.Action.ACCESS,
            actor=self.normal_user,
            additional_data={
                'entity_type': 'user',
                'action_type': 'login',
                'company_id': str(self.company.id),
                'company_name': self.company.name,
            }
        )
        
    def test_summary_report(self):
        """Tests if the summarized report works correctly."""
        url = reverse('reporting:audit-summary-report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('data' in response.data)
        data = response.data['data']
        
        # Verify if metrics are present
        self.assertTrue('action_distribution' in data)
        self.assertTrue('entity_distribution' in data)
        self.assertTrue('time_series' in data)
        self.assertTrue('top_users' in data)
        
        # Verify if totals are correct
        self.assertTrue(data['total_logs'] >= 3)  # At least the logs we created
        
    def test_user_activity_report(self):
        """Tests if the user activity report works."""
        url = reverse('reporting:user-activity-report')
        response = self.client.get(url, {'user_id': self.normal_user.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('data' in response.data)
        data = response.data['data']
        
        # Verify if metrics are present
        self.assertTrue('action_distribution' in data)
        self.assertTrue('entity_distribution' in data)
        self.assertTrue('time_series' in data)
        
        # Verify if user data is correct
        self.assertEqual(data['user_id'], str(self.normal_user.id))
        self.assertEqual(data['username'], self.normal_user.username)
        
        # Verify if total is correct
        self.assertTrue(data['total_actions'] >= 2)  # At least the logs we created
        
    def test_user_activity_report_requires_user_id(self):
        """Tests if the user activity report requires user_id."""
        url = reverse('reporting:user-activity-report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_filtering_by_entity_type_in_report(self):
        """Tests if filtering by entity type works in reports."""
        url = reverse('reporting:audit-summary-report')
        response = self.client.get(url, {'entity_type': 'alert'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        
        # Verify entity distribution
        if data['entity_distribution']:
            for entity in data['entity_distribution']:
                self.assertEqual(entity['entity_type'], 'alert')
                
    def test_filtering_by_period_in_report(self):
        """Tests if filtering by period works in reports."""
        url = reverse('reporting:audit-summary-report')
        response = self.client.get(url, {'period': 'today'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK) 