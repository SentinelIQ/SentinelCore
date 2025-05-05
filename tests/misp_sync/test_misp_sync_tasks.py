from django.test import TestCase
from unittest.mock import patch, MagicMock
from misp_sync.tasks import (
    sync_misp_events,
    sync_misp_objects,
    sync_misp_attributes,
    sync_all_misp_data
)
from misp_sync.models import MISPEvent, MISPObject, MISPAttribute
from api.core.test_utils import APITestCaseMixin
from api.core.tasks import audit_task

class MISPSyncTaskTests(APITestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.setup_tenant()
        self.setup_user()
        self.setup_company()
        self.setup_company_member()
        self.setup_company_analyst()
        self.setup_company_admin()
        self.setup_superuser()

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_events_task(self, mock_get):
        """Test MISP events synchronization task"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Event": [{
                "id": 1,
                "info": "Test Event",
                "threat_level_id": 1,
                "analysis": 0,
                "date": "2024-01-01",
                "published": True,
                "uuid": "test-uuid",
                "timestamp": 1234567890,
                "distribution": 0,
                "sharing_group_id": 0,
                "org_id": 1,
                "orgc_id": 1,
                "attribute_count": 0
            }]
        }
        mock_get.return_value = mock_response

        result = sync_misp_events(self.company.id)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(MISPEvent.objects.count(), 1)

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_objects_task(self, mock_get):
        """Test MISP objects synchronization task"""
        event = MISPEvent.objects.create(
            event_id=1,
            info="Test Event",
            threat_level_id=1,
            analysis=0,
            date="2024-01-01",
            published=True,
            uuid="test-uuid",
            timestamp=1234567890,
            distribution=0,
            sharing_group_id=0,
            org_id=1,
            orgc_id=1,
            attribute_count=0,
            company=self.company
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Object": [{
                "id": 1,
                "name": "test-object",
                "meta-category": "test-category",
                "description": "Test Description",
                "template_uuid": "test-template-uuid",
                "template_version": "1",
                "event_id": 1,
                "uuid": "test-uuid",
                "timestamp": 1234567890,
                "distribution": 0,
                "sharing_group_id": 0,
                "comment": "Test Comment",
                "deleted": False
            }]
        }
        mock_get.return_value = mock_response

        result = sync_misp_objects(self.company.id)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(MISPObject.objects.count(), 1)

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_attributes_task(self, mock_get):
        """Test MISP attributes synchronization task"""
        event = MISPEvent.objects.create(
            event_id=1,
            info="Test Event",
            threat_level_id=1,
            analysis=0,
            date="2024-01-01",
            published=True,
            uuid="test-uuid",
            timestamp=1234567890,
            distribution=0,
            sharing_group_id=0,
            org_id=1,
            orgc_id=1,
            attribute_count=0,
            company=self.company
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Attribute": [{
                "id": 1,
                "type": "ip-src",
                "category": "Network activity",
                "to_ids": True,
                "uuid": "test-uuid",
                "event_id": 1,
                "distribution": 0,
                "timestamp": 1234567890,
                "comment": "Test Comment",
                "sharing_group_id": 0,
                "deleted": False,
                "disable_correlation": False,
                "object_id": 0,
                "object_relation": None,
                "value": "192.168.1.1",
                "first_seen": "2024-01-01T00:00:00Z",
                "last_seen": "2024-01-01T00:00:00Z"
            }]
        }
        mock_get.return_value = mock_response

        result = sync_misp_attributes(self.company.id)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(MISPAttribute.objects.count(), 1)

    @patch('misp_sync.tasks.sync_misp_events')
    @patch('misp_sync.tasks.sync_misp_objects')
    @patch('misp_sync.tasks.sync_misp_attributes')
    def test_sync_all_misp_data_task(self, mock_sync_attrs, mock_sync_objs, mock_sync_events):
        """Test complete MISP data synchronization task"""
        mock_sync_events.return_value = {'status': 'success'}
        mock_sync_objs.return_value = {'status': 'success'}
        mock_sync_attrs.return_value = {'status': 'success'}

        result = sync_all_misp_data(self.company.id)
        self.assertEqual(result['status'], 'success')
        mock_sync_events.assert_called_once_with(self.company.id)
        mock_sync_objs.assert_called_once_with(self.company.id)
        mock_sync_attrs.assert_called_once_with(self.company.id)

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_events_error_handling(self, mock_get):
        """Test error handling in MISP events synchronization"""
        mock_get.side_effect = Exception("API Error")

        result = sync_misp_events(self.company.id)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(MISPEvent.objects.count(), 0)

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_objects_error_handling(self, mock_get):
        """Test error handling in MISP objects synchronization"""
        mock_get.side_effect = Exception("API Error")

        result = sync_misp_objects(self.company.id)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(MISPObject.objects.count(), 0)

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_attributes_error_handling(self, mock_get):
        """Test error handling in MISP attributes synchronization"""
        mock_get.side_effect = Exception("API Error")

        result = sync_misp_attributes(self.company.id)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(MISPAttribute.objects.count(), 0)

    @patch('misp_sync.tasks.audit_task')
    def test_audit_logging_in_tasks(self, mock_audit_task):
        """Test audit logging in MISP sync tasks"""
        mock_audit_task.return_value = {'status': 'success'}

        result = sync_misp_events(self.company.id)
        mock_audit_task.assert_called()
        self.assertEqual(result['status'], 'success') 