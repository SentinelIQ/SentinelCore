from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from api.core.test_utils import APITestCaseMixin
from misp_sync.models import MISPEvent, MISPObject, MISPAttribute
from misp_sync.serializers import MISPEventSerializer, MISPObjectSerializer, MISPAttributeSerializer
from misp_sync.views import MISPEventViewSet, MISPObjectViewSet, MISPAttributeViewSet
from misp_sync.tasks import sync_misp_events, sync_misp_objects, sync_misp_attributes
from unittest.mock import patch, MagicMock
import json

class MISPSyncViewTests(APITestCaseMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.setup_tenant()
        self.setup_user()
        self.setup_company()
        self.setup_company_member()
        self.setup_company_analyst()
        self.setup_company_admin()
        self.setup_superuser()

    def test_misp_event_list(self):
        """Test listing MISP events"""
        url = reverse('misp-event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    def test_misp_event_detail(self):
        """Test retrieving a specific MISP event"""
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
        url = reverse('misp-event-detail', args=[event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['info'], "Test Event")

    def test_misp_object_list(self):
        """Test listing MISP objects"""
        url = reverse('misp-object-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    def test_misp_attribute_list(self):
        """Test listing MISP attributes"""
        url = reverse('misp-attribute-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_events(self, mock_get):
        """Test MISP events synchronization"""
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

        url = reverse('misp-event-sync')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(MISPEvent.objects.count(), 1)

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_objects(self, mock_get):
        """Test MISP objects synchronization"""
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

        url = reverse('misp-object-sync')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(MISPObject.objects.count(), 1)

    @patch('misp_sync.tasks.requests.get')
    def test_sync_misp_attributes(self, mock_get):
        """Test MISP attributes synchronization"""
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

        url = reverse('misp-attribute-sync')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(MISPAttribute.objects.count(), 1)

    def test_misp_event_permissions(self):
        """Test MISP event permissions"""
        url = reverse('misp-event-list')
        
        # Test unauthenticated access
        self.client.credentials()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test authenticated user access
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_misp_object_permissions(self):
        """Test MISP object permissions"""
        url = reverse('misp-object-list')
        
        # Test unauthenticated access
        self.client.credentials()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test authenticated user access
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_misp_attribute_permissions(self):
        """Test MISP attribute permissions"""
        url = reverse('misp-attribute-list')
        
        # Test unauthenticated access
        self.client.credentials()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test authenticated user access
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) 