"""
Tests for the audit log system.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from companies.models import Company
from django.contrib.contenttypes.models import ContentType
from api.v1.audit_logs.enums import EntityTypeEnum
from api.core.audit import AuditLogMixin, audit_action
from api.core.audit import audit_task, AuditLogTaskMixin
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
import logging
import json
from unittest.mock import patch, MagicMock

User = get_user_model()
logger = logging.getLogger('test')


class AuditLogModelTest(TestCase):
    """
    Test the LogEntry model functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
            domain="testcompany.com"
        )
        
        # Create a superuser and a regular user
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="super@example.com",
            password="password123"
        )
        
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
            company=self.company
        )
        
        # Set up API client
        self.client = APIClient()
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up test data
        LogEntry.objects.all().delete()
    
    def test_log_create_creates_log_entry(self):
        """Test that log_create method creates a log entry."""
        # Get the content type for User
        content_type = ContentType.objects.get_for_model(User)
        
        # Create a log entry using log_create
        LogEntry.objects.log_create(
            instance=self.user,
            action=LogEntry.Action.CREATE,
            changes={},
            actor=self.user,
            additional_data={
                'entity_type': EntityTypeEnum.USER.value,
                'company_id': str(self.company.id),
                'company_name': self.company.name
            }
        )
        
        # Verify the log entry was created
        logs = LogEntry.objects.all()
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertEqual(log.content_type, content_type)
        self.assertEqual(log.object_pk, str(self.user.pk))
        self.assertEqual(log.action, LogEntry.Action.CREATE)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.additional_data['entity_type'], EntityTypeEnum.USER.value)
        self.assertEqual(log.additional_data['company_id'], str(self.company.id))
    
    def test_create_log_with_anonymous_user(self):
        """Test creating log entry with anonymous user."""
        # Create a log entry without an actor
        LogEntry.objects.log_create(
            instance=self.user,
            action=LogEntry.Action.CREATE,
            changes={},
            actor=None,
            additional_data={
                'entity_type': EntityTypeEnum.USER.value,
                'company_id': str(self.company.id),
                'company_name': self.company.name
            }
        )
        
        # Verify the log entry was created without an actor
        logs = LogEntry.objects.all()
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertIsNone(log.actor)
        self.assertEqual(log.additional_data['entity_type'], EntityTypeEnum.USER.value)
    
    def test_create_log_with_system_actor(self):
        """Test creating log entry with system actor information."""
        # Create a log entry with system actor information
        LogEntry.objects.log_create(
            instance=self.user,
            action=LogEntry.Action.CREATE,
            changes={},
            actor=None,
            additional_data={
                'entity_type': EntityTypeEnum.USER.value,
                'company_id': str(self.company.id),
                'system_actor': 'system.celery.task'
            }
        )
        
        # Verify the log entry was created
        logs = LogEntry.objects.all()
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertIsNone(log.actor)
        self.assertEqual(log.additional_data['system_actor'], 'system.celery.task')
        self.assertEqual(log.additional_data['entity_type'], EntityTypeEnum.USER.value)
    
    def test_sanitizes_sensitive_data(self):
        """Test that sensitive data is sanitized by our mixin."""
        # Create a mixin instance to use its sanitization method
        mixin = AuditLogMixin()
        
        # Test data with sensitive information
        request_data = {
            "username": "test",
            "password": "secret123",
            "token": "sensitive-token",
            "email": "user@example.com"
        }
        
        # Sanitize the data
        sanitized = mixin._sanitize_data(request_data)
        
        # Verify sensitive fields are masked
        self.assertEqual(sanitized["username"], "test")
        self.assertEqual(sanitized["password"], "******")
        self.assertEqual(sanitized["token"], "******")
        self.assertEqual(sanitized["email"], "user@example.com")


class MockRequest:
    """Mock request object for testing."""
    def __init__(self, user=None, method='GET', path='/', query_params=None):
        self.user = user
        self.method = method
        self.path = path
        self.META = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_USER_AGENT': 'Test Agent'}
        self.query_params = query_params or {}
        self.data = {}


class TestModel:
    """Mock model for testing."""
    def __init__(self, id=1, name="Test Object"):
        self.id = id
        self.name = name
        self.pk = id
        self.company = None
    
    def __str__(self):
        return self.name


class AuditLogMixinTest(TestCase):
    """
    Test the AuditLogMixin functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
            domain="testcompany.com"
        )
        
        # Create a user
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
            company=self.company
        )
        
        # Create a test object
        self.test_obj = TestModel()
        self.test_obj.company = self.company
        
        # Mock request
        self.mock_request = MockRequest(user=self.user)
        
        # Create test view with mixin
        class TestViewSet(AuditLogMixin, viewsets.ViewSet):
            entity_type = 'test'
            
            def __init__(self, request=None):
                self.request = request
        
        self.view = TestViewSet(request=self.mock_request)
    
    def tearDown(self):
        """Clean up after tests."""
        LogEntry.objects.all().delete()
    
    @patch('auditlog.models.LogEntry.objects.log_create')
    def test_perform_create(self, mock_log_create):
        """Test that perform_create calls log_create."""
        # Mock serializer
        class MockSerializer:
            def save(self):
                return TestModel(id=1, name="Test Object")
        
        # Call perform_create
        serializer = MockSerializer()
        self.view.perform_create(serializer)
        
        # Verify log_create was called
        mock_log_create.assert_called_once()
        args, kwargs = mock_log_create.call_args
        self.assertEqual(kwargs['action'], LogEntry.Action.CREATE)
        self.assertEqual(kwargs['actor'], self.user)
        self.assertEqual(kwargs['additional_data']['entity_type'], 'test')
    
    @patch('auditlog.models.LogEntry.objects.log_create')
    def test_perform_update(self, mock_log_create):
        """Test that perform_update calls log_create."""
        # Mock serializer
        class MockSerializer:
            instance = TestModel(id=1, name="Updated Object")
            validated_data = {'name': 'Updated Object', 'description': 'New description'}
            
            def save(self):
                return self.instance
        
        # Call perform_update
        serializer = MockSerializer()
        self.view.perform_update(serializer)
        
        # Verify log_create was called
        mock_log_create.assert_called_once()
        args, kwargs = mock_log_create.call_args
        self.assertEqual(kwargs['action'], LogEntry.Action.UPDATE)
        self.assertEqual(kwargs['actor'], self.user)
        self.assertEqual(kwargs['additional_data']['entity_type'], 'test')
        self.assertEqual(kwargs['additional_data']['changed_fields'], 
                        list(serializer.validated_data.keys()))
    
    @patch('auditlog.models.LogEntry.objects.log_create')
    def test_perform_destroy(self, mock_log_create):
        """Test that perform_destroy calls log_create."""
        # Create a mock TestModel with a delete method
        test_obj = TestModel(id=1, name="Test Object")
        test_obj.delete = MagicMock()
        
        # Call perform_destroy
        self.view.perform_destroy(test_obj)
        
        # Verify log_create was called before deletion
        mock_log_create.assert_called_once()
        args, kwargs = mock_log_create.call_args
        self.assertEqual(kwargs['action'], LogEntry.Action.DELETE)
        self.assertEqual(kwargs['actor'], self.user)
        self.assertEqual(kwargs['additional_data']['entity_type'], 'test')
        
        # Verify delete was called
        test_obj.delete.assert_called_once()


class AuditActionDecoratorTest(TestCase):
    """
    Test the audit_action decorator functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
            domain="testcompany.com"
        )
        
        # Create a user
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
            company=self.company
        )
        
        # Mock request
        self.mock_request = MockRequest(user=self.user)
        
        # Create test view with decorated method
        class TestViewSet:
            entity_type = 'test'
            
            def __init__(self, request=None):
                self.request = request
            
            @audit_action(action_type='custom', entity_type='test')
            def custom_action(self, request, pk=None):
                return Response({"status": "success"})
        
        self.view = TestViewSet(request=self.mock_request)
    
    def tearDown(self):
        """Clean up after tests."""
        LogEntry.objects.all().delete()
    
    @patch('auditlog.models.LogEntry.objects.create')
    def test_audit_action_decorator(self, mock_create):
        """Test that audit_action decorator logs the action."""
        # Call the decorated method
        response = self.view.custom_action(self.mock_request, pk='123')
        
        # Verify LogEntry.objects.create was called
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        self.assertEqual(kwargs['action'], LogEntry.Action.CREATE)
        self.assertEqual(kwargs['actor'], self.user)
        self.assertTrue('entity_type' in kwargs['additional_data'])
        self.assertEqual(kwargs['additional_data']['entity_type'], 'test')
        self.assertTrue('custom_action' in kwargs['additional_data'])
        self.assertEqual(kwargs['additional_data']['custom_action'], 'custom_action')


class CeleryAuditTest(TestCase):
    """
    Test the Celery audit functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
            domain="testcompany.com"
        )
        
        # Create a user
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
            company=self.company
        )
    
    def tearDown(self):
        """Clean up after tests."""
        LogEntry.objects.all().delete()
    
    @patch('celery._state.get_current_task')
    @patch('auditlog.models.LogEntry.objects.create')
    def test_audit_task_decorator(self, mock_create, mock_get_current_task):
        """Test that audit_task decorator logs task events."""
        # Mock celery task
        mock_task = MagicMock()
        mock_task.request.id = 'test-task-id'
        mock_task.name = 'test_task'
        mock_get_current_task.return_value = mock_task
        
        # Define a decorated task function
        @audit_task(entity_type='alert')
        def process_alert(alert_id, **kwargs):
            return f"Processed alert {alert_id}"
        
        # Call the decorated function
        result = process_alert('123', company_id='456')
        
        # Verify LogEntry.objects.create was called for task start
        self.assertEqual(mock_create.call_count, 2)
        
        # Check start log
        start_call = mock_create.call_args_list[0]
        self.assertEqual(start_call[1]['action'], LogEntry.Action.CREATE)
        self.assertEqual(start_call[1]['additional_data']['status'], 'started')
        self.assertEqual(start_call[1]['additional_data']['entity_type'], 'alert')
        
        # Check success log
        success_call = mock_create.call_args_list[1]
        self.assertEqual(success_call[1]['action'], LogEntry.Action.UPDATE)
        self.assertEqual(success_call[1]['additional_data']['status'], 'success')
        self.assertEqual(success_call[1]['additional_data']['result'], 'Processed alert 123')
    
    @patch('celery._state.get_current_task')
    @patch('auditlog.models.LogEntry.objects.create')
    def test_audit_task_decorator_exception(self, mock_create, mock_get_current_task):
        """Test that audit_task decorator logs task failures."""
        # Mock celery task
        mock_task = MagicMock()
        mock_task.request.id = 'test-task-id'
        mock_task.name = 'test_task'
        mock_get_current_task.return_value = mock_task
        
        # Define a decorated task function that raises an exception
        @audit_task(entity_type='alert')
        def process_alert_with_error(alert_id, **kwargs):
            raise ValueError("Test error")
        
        # Call the decorated function and catch the exception
        try:
            process_alert_with_error('123', company_id='456')
        except ValueError:
            pass
        
        # Verify LogEntry.objects.create was called for task start and failure
        self.assertEqual(mock_create.call_count, 2)
        
        # Check start log
        start_call = mock_create.call_args_list[0]
        self.assertEqual(start_call[1]['action'], LogEntry.Action.CREATE)
        self.assertEqual(start_call[1]['additional_data']['status'], 'started')
        
        # Check failure log
        failure_call = mock_create.call_args_list[1]
        self.assertEqual(failure_call[1]['action'], LogEntry.Action.UPDATE)
        self.assertEqual(failure_call[1]['additional_data']['status'], 'failure')
        self.assertEqual(failure_call[1]['additional_data']['error_type'], 'ValueError')
        self.assertEqual(failure_call[1]['additional_data']['error'], 'Test error')


class AuditLogAPITest(TestCase):
    """
    Test the Audit Log API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
            domain="testcompany.com"
        )
        
        # Create a superuser and a regular user
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="super@example.com",
            password="password123"
        )
        
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
            company=self.company
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Create some log entries for testing
        for i in range(5):
            LogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(User),
                object_pk=str(self.user.pk),
                object_repr=str(self.user),
                action=LogEntry.Action.CREATE,
                changes='{}',
                actor=self.superuser,
                remote_addr='127.0.0.1',
                additional_data={
                    'entity_type': EntityTypeEnum.USER.value,
                    'company_id': str(self.company.id),
                    'company_name': self.company.name,
                    'request_method': 'POST',
                    'request_path': f'/api/v1/users/{i}/'
                }
            )
    
    def tearDown(self):
        """Clean up after tests."""
        LogEntry.objects.all().delete()
    
    def test_list_audit_logs_as_superuser(self):
        """Test listing audit logs as superuser."""
        # Login as superuser
        self.client.force_authenticate(user=self.superuser)
        
        # Get list of audit logs
        response = self.client.get(reverse('auditlog-list'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 5)
    
    def test_list_audit_logs_as_regular_user(self):
        """Test listing audit logs as regular user (company-scoped)."""
        # Login as regular user
        self.client.force_authenticate(user=self.user)
        
        # Get list of audit logs
        response = self.client.get(reverse('auditlog-list'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        # Should only see logs from their company
        self.assertEqual(len(response.data['data']), 5)
    
    def test_filter_audit_logs_by_entity_type(self):
        """Test filtering audit logs by entity type."""
        # Create log for a different entity type
        LogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Company),
            object_pk=str(self.company.pk),
            object_repr=str(self.company),
            action=LogEntry.Action.UPDATE,
            changes='{}',
            actor=self.superuser,
            remote_addr='127.0.0.1',
            additional_data={
                'entity_type': EntityTypeEnum.COMPANY.value,
                'company_id': str(self.company.id),
                'company_name': self.company.name
            }
        )
        
        # Login as superuser
        self.client.force_authenticate(user=self.superuser)
        
        # Filter by entity_type=user
        response = self.client.get(
            reverse('auditlog-list'), 
            {'entity_type': EntityTypeEnum.USER.value}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 5)
        
        # Filter by entity_type=company
        response = self.client.get(
            reverse('auditlog-list'), 
            {'entity_type': EntityTypeEnum.COMPANY.value}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
    
    def test_retrieve_audit_log(self):
        """Test retrieving a specific audit log."""
        # Login as superuser
        self.client.force_authenticate(user=self.superuser)
        
        # Get a log entry ID
        log = LogEntry.objects.first()
        
        # Get the audit log
        response = self.client.get(reverse('auditlog-detail', args=[log.id]))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['id'], str(log.id))
    
    @patch('api.v1.audit_logs.views.AuditLogViewSet._export_csv')
    def test_export_audit_logs_csv(self, mock_export_csv):
        """Test exporting audit logs as CSV."""
        # Mock the CSV export method
        mock_response = Response(content="test,csv,data")
        mock_export_csv.return_value = mock_response
        
        # Login as superuser
        self.client.force_authenticate(user=self.superuser)
        
        # Export audit logs
        response = self.client.get(reverse('auditlog-export'))
        
        # Check that export method was called
        mock_export_csv.assert_called_once()
        
        # Check response
        self.assertEqual(response.content, b'test,csv,data')
    
    @patch('api.v1.audit_logs.views.AuditLogViewSet._export_json')
    def test_export_audit_logs_json(self, mock_export_json):
        """Test exporting audit logs as JSON."""
        # Mock the JSON export method
        mock_response = Response(content='{"data": "test"}')
        mock_export_json.return_value = mock_response
        
        # Login as superuser
        self.client.force_authenticate(user=self.superuser)
        
        # Export audit logs as JSON
        response = self.client.get(
            reverse('auditlog-export'), 
            {'format': 'json'}
        )
        
        # Check that export method was called
        mock_export_json.assert_called_once()
        
        # Check response
        self.assertEqual(response.content, b'{"data": "test"}')
    
    @patch('api.v1.audit_logs.views.AuditLogViewSet._export_excel')
    def test_export_audit_logs_excel(self, mock_export_excel):
        """Test exporting audit logs as Excel."""
        # Mock the Excel export method
        mock_response = Response(content=b'excel-data')
        mock_export_excel.return_value = mock_response
        
        # Login as superuser
        self.client.force_authenticate(user=self.superuser)
        
        # Export audit logs as Excel
        response = self.client.get(
            reverse('auditlog-export'), 
            {'format': 'excel'}
        )
        
        # Check that export method was called
        mock_export_excel.assert_called_once()
        
        # Check response
        self.assertEqual(response.content, b'excel-data') 