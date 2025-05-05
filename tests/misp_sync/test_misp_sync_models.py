from django.test import TestCase
from misp_sync.models import MISPEvent, MISPObject, MISPAttribute
from api.core.test_utils import APITestCaseMixin

class MISPSyncModelTests(APITestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.setup_tenant()
        self.setup_user()
        self.setup_company()
        self.setup_company_member()
        self.setup_company_analyst()
        self.setup_company_admin()
        self.setup_superuser()

    def test_misp_event_creation(self):
        """Test MISP event model creation"""
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

        self.assertEqual(event.info, "Test Event")
        self.assertEqual(event.threat_level_id, 1)
        self.assertTrue(event.published)
        self.assertEqual(event.company, self.company)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_misp_object_creation(self):
        """Test MISP object model creation"""
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

        self.assertEqual(obj.name, "test-object")
        self.assertEqual(obj.meta_category, "test-category")
        self.assertEqual(obj.event, event)
        self.assertEqual(obj.company, self.company)
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)

    def test_misp_attribute_creation(self):
        """Test MISP attribute model creation"""
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

        self.assertEqual(attr.type, "ip-src")
        self.assertEqual(attr.category, "Network activity")
        self.assertTrue(attr.to_ids)
        self.assertEqual(attr.event, event)
        self.assertEqual(attr.value, "192.168.1.1")
        self.assertEqual(attr.company, self.company)
        self.assertIsNotNone(attr.created_at)
        self.assertIsNotNone(attr.updated_at)

    def test_misp_event_str_representation(self):
        """Test MISP event string representation"""
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

        self.assertEqual(str(event), "Test Event (1)")

    def test_misp_object_str_representation(self):
        """Test MISP object string representation"""
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

        self.assertEqual(str(obj), "test-object (1)")

    def test_misp_attribute_str_representation(self):
        """Test MISP attribute string representation"""
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

        self.assertEqual(str(attr), "ip-src: 192.168.1.1 (1)")

    def test_misp_event_relationships(self):
        """Test MISP event relationships"""
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

        self.assertEqual(event.objects.count(), 1)
        self.assertEqual(event.attributes.count(), 1)
        self.assertEqual(obj.event, event)
        self.assertEqual(attr.event, event) 