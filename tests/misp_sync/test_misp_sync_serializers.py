from django.test import TestCase
from misp_sync.models import MISPEvent, MISPObject, MISPAttribute
from misp_sync.serializers import (
    MISPEventSerializer,
    MISPObjectSerializer,
    MISPAttributeSerializer
)
from api.core.test_utils import APITestCaseMixin

class MISPSyncSerializerTests(APITestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.setup_tenant()
        self.setup_user()
        self.setup_company()
        self.setup_company_member()
        self.setup_company_analyst()
        self.setup_company_admin()
        self.setup_superuser()

    def test_misp_event_serializer(self):
        """Test MISP event serializer"""
        event_data = {
            "event_id": 1,
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
            "attribute_count": 0,
            "company": self.company.id
        }

        serializer = MISPEventSerializer(data=event_data)
        self.assertTrue(serializer.is_valid())
        event = serializer.save()

        self.assertEqual(event.info, "Test Event")
        self.assertEqual(event.threat_level_id, 1)
        self.assertTrue(event.published)
        self.assertEqual(event.company, self.company)

    def test_misp_object_serializer(self):
        """Test MISP object serializer"""
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

        object_data = {
            "object_id": 1,
            "name": "test-object",
            "meta_category": "test-category",
            "description": "Test Description",
            "template_uuid": "test-template-uuid",
            "template_version": "1",
            "event": event.id,
            "uuid": "test-uuid",
            "timestamp": 1234567890,
            "distribution": 0,
            "sharing_group_id": 0,
            "comment": "Test Comment",
            "deleted": False,
            "company": self.company.id
        }

        serializer = MISPObjectSerializer(data=object_data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()

        self.assertEqual(obj.name, "test-object")
        self.assertEqual(obj.meta_category, "test-category")
        self.assertEqual(obj.event, event)
        self.assertEqual(obj.company, self.company)

    def test_misp_attribute_serializer(self):
        """Test MISP attribute serializer"""
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

        attribute_data = {
            "attribute_id": 1,
            "type": "ip-src",
            "category": "Network activity",
            "to_ids": True,
            "uuid": "test-uuid",
            "event": event.id,
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
            "last_seen": "2024-01-01T00:00:00Z",
            "company": self.company.id
        }

        serializer = MISPAttributeSerializer(data=attribute_data)
        self.assertTrue(serializer.is_valid())
        attr = serializer.save()

        self.assertEqual(attr.type, "ip-src")
        self.assertEqual(attr.category, "Network activity")
        self.assertTrue(attr.to_ids)
        self.assertEqual(attr.event, event)
        self.assertEqual(attr.value, "192.168.1.1")
        self.assertEqual(attr.company, self.company)

    def test_misp_event_serializer_validation(self):
        """Test MISP event serializer validation"""
        invalid_data = {
            "event_id": "invalid",  # Should be integer
            "info": "",  # Should not be empty
            "threat_level_id": 5,  # Should be between 1 and 4
            "published": "invalid"  # Should be boolean
        }

        serializer = MISPEventSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("event_id", serializer.errors)
        self.assertIn("info", serializer.errors)
        self.assertIn("threat_level_id", serializer.errors)
        self.assertIn("published", serializer.errors)

    def test_misp_object_serializer_validation(self):
        """Test MISP object serializer validation"""
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

        invalid_data = {
            "object_id": "invalid",  # Should be integer
            "name": "",  # Should not be empty
            "event": 999,  # Non-existent event
            "deleted": "invalid"  # Should be boolean
        }

        serializer = MISPObjectSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("object_id", serializer.errors)
        self.assertIn("name", serializer.errors)
        self.assertIn("event", serializer.errors)
        self.assertIn("deleted", serializer.errors)

    def test_misp_attribute_serializer_validation(self):
        """Test MISP attribute serializer validation"""
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

        invalid_data = {
            "attribute_id": "invalid",  # Should be integer
            "type": "",  # Should not be empty
            "category": "",  # Should not be empty
            "event": 999,  # Non-existent event
            "value": "",  # Should not be empty
            "to_ids": "invalid"  # Should be boolean
        }

        serializer = MISPAttributeSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("attribute_id", serializer.errors)
        self.assertIn("type", serializer.errors)
        self.assertIn("category", serializer.errors)
        self.assertIn("event", serializer.errors)
        self.assertIn("value", serializer.errors)
        self.assertIn("to_ids", serializer.errors)

    def test_misp_event_serializer_update(self):
        """Test MISP event serializer update"""
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

        update_data = {
            "info": "Updated Event",
            "threat_level_id": 2,
            "published": False
        }

        serializer = MISPEventSerializer(event, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_event = serializer.save()

        self.assertEqual(updated_event.info, "Updated Event")
        self.assertEqual(updated_event.threat_level_id, 2)
        self.assertFalse(updated_event.published)

    def test_misp_object_serializer_update(self):
        """Test MISP object serializer update"""
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

        obj = MISPObject.objects.create(
            object_id=1,
            name="test-object",
            meta_category="test-category",
            description="Test Description",
            template_uuid="test-template-uuid",
            template_version="1",
            event=event,
            uuid="test-uuid",
            timestamp=1234567890,
            distribution=0,
            sharing_group_id=0,
            comment="Test Comment",
            deleted=False,
            company=self.company
        )

        update_data = {
            "name": "Updated Object",
            "description": "Updated Description",
            "deleted": True
        }

        serializer = MISPObjectSerializer(obj, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_obj = serializer.save()

        self.assertEqual(updated_obj.name, "Updated Object")
        self.assertEqual(updated_obj.description, "Updated Description")
        self.assertTrue(updated_obj.deleted)

    def test_misp_attribute_serializer_update(self):
        """Test MISP attribute serializer update"""
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

        attr = MISPAttribute.objects.create(
            attribute_id=1,
            type="ip-src",
            category="Network activity",
            to_ids=True,
            uuid="test-uuid",
            event=event,
            distribution=0,
            timestamp=1234567890,
            comment="Test Comment",
            sharing_group_id=0,
            deleted=False,
            disable_correlation=False,
            object_id=0,
            object_relation=None,
            value="192.168.1.1",
            first_seen="2024-01-01T00:00:00Z",
            last_seen="2024-01-01T00:00:00Z",
            company=self.company
        )

        update_data = {
            "type": "ip-dst",
            "value": "192.168.1.2",
            "to_ids": False
        }

        serializer = MISPAttributeSerializer(attr, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_attr = serializer.save()

        self.assertEqual(updated_attr.type, "ip-dst")
        self.assertEqual(updated_attr.value, "192.168.1.2")
        self.assertFalse(updated_attr.to_ids) 