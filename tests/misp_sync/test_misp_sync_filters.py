from django.test import TestCase
from django_filters import FilterSet
from misp_sync.models import MISPEvent, MISPObject, MISPAttribute
from misp_sync.filters import (
    MISPEventFilter,
    MISPObjectFilter,
    MISPAttributeFilter
)
from api.core.test_utils import APITestCaseMixin

class MISPSyncFilterTests(APITestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.setup_tenant()
        self.setup_user()
        self.setup_company()
        self.setup_company_member()
        self.setup_company_analyst()
        self.setup_company_admin()
        self.setup_superuser()

    def test_misp_event_filter(self):
        """Test MISP event filtering"""
        # Create test events
        event1 = MISPEvent.objects.create(
            event_id=1,
            info="Test Event 1",
            threat_level_id=1,
            analysis=0,
            date="2024-01-01",
            published=True,
            uuid="test-uuid-1",
            timestamp=1234567890,
            distribution=0,
            sharing_group_id=0,
            org_id=1,
            orgc_id=1,
            attribute_count=0,
            company=self.company
        )

        event2 = MISPEvent.objects.create(
            event_id=2,
            info="Test Event 2",
            threat_level_id=2,
            analysis=1,
            date="2024-01-02",
            published=False,
            uuid="test-uuid-2",
            timestamp=1234567891,
            distribution=1,
            sharing_group_id=1,
            org_id=2,
            orgc_id=2,
            attribute_count=1,
            company=self.company
        )

        # Test filtering by info
        filter_set = MISPEventFilter({'info': 'Test Event 1'}, queryset=MISPEvent.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), event1)

        # Test filtering by threat_level_id
        filter_set = MISPEventFilter({'threat_level_id': 2}, queryset=MISPEvent.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), event2)

        # Test filtering by published status
        filter_set = MISPEventFilter({'published': True}, queryset=MISPEvent.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), event1)

        # Test filtering by date range
        filter_set = MISPEventFilter({
            'date_after': '2024-01-01',
            'date_before': '2024-01-01'
        }, queryset=MISPEvent.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), event1)

    def test_misp_object_filter(self):
        """Test MISP object filtering"""
        # Create test event
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

        # Create test objects
        obj1 = MISPObject.objects.create(
            object_id=1,
            name="test-object-1",
            meta_category="test-category-1",
            description="Test Description 1",
            template_uuid="test-template-uuid-1",
            template_version="1",
            event=event,
            uuid="test-uuid-1",
            timestamp=1234567890,
            distribution=0,
            sharing_group_id=0,
            comment="Test Comment 1",
            deleted=False,
            company=self.company
        )

        obj2 = MISPObject.objects.create(
            object_id=2,
            name="test-object-2",
            meta_category="test-category-2",
            description="Test Description 2",
            template_uuid="test-template-uuid-2",
            template_version="2",
            event=event,
            uuid="test-uuid-2",
            timestamp=1234567891,
            distribution=1,
            sharing_group_id=1,
            comment="Test Comment 2",
            deleted=True,
            company=self.company
        )

        # Test filtering by name
        filter_set = MISPObjectFilter({'name': 'test-object-1'}, queryset=MISPObject.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), obj1)

        # Test filtering by meta_category
        filter_set = MISPObjectFilter({'meta_category': 'test-category-2'}, queryset=MISPObject.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), obj2)

        # Test filtering by deleted status
        filter_set = MISPObjectFilter({'deleted': False}, queryset=MISPObject.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), obj1)

        # Test filtering by event
        filter_set = MISPObjectFilter({'event': event.id}, queryset=MISPObject.objects.all())
        self.assertEqual(filter_set.qs.count(), 2)

    def test_misp_attribute_filter(self):
        """Test MISP attribute filtering"""
        # Create test event
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

        # Create test attributes
        attr1 = MISPAttribute.objects.create(
            attribute_id=1,
            type="ip-src",
            category="Network activity",
            to_ids=True,
            uuid="test-uuid-1",
            event=event,
            distribution=0,
            timestamp=1234567890,
            comment="Test Comment 1",
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

        attr2 = MISPAttribute.objects.create(
            attribute_id=2,
            type="ip-dst",
            category="Network activity",
            to_ids=False,
            uuid="test-uuid-2",
            event=event,
            distribution=1,
            timestamp=1234567891,
            comment="Test Comment 2",
            sharing_group_id=1,
            deleted=True,
            disable_correlation=True,
            object_id=0,
            object_relation=None,
            value="192.168.1.2",
            first_seen="2024-01-02T00:00:00Z",
            last_seen="2024-01-02T00:00:00Z",
            company=self.company
        )

        # Test filtering by type
        filter_set = MISPAttributeFilter({'type': 'ip-src'}, queryset=MISPAttribute.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), attr1)

        # Test filtering by category
        filter_set = MISPAttributeFilter({'category': 'Network activity'}, queryset=MISPAttribute.objects.all())
        self.assertEqual(filter_set.qs.count(), 2)

        # Test filtering by to_ids
        filter_set = MISPAttributeFilter({'to_ids': True}, queryset=MISPAttribute.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), attr1)

        # Test filtering by value
        filter_set = MISPAttributeFilter({'value': '192.168.1.2'}, queryset=MISPAttribute.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), attr2)

        # Test filtering by first_seen range
        filter_set = MISPAttributeFilter({
            'first_seen_after': '2024-01-02T00:00:00Z',
            'first_seen_before': '2024-01-02T00:00:00Z'
        }, queryset=MISPAttribute.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), attr2)

        # Test filtering by last_seen range
        filter_set = MISPAttributeFilter({
            'last_seen_after': '2024-01-01T00:00:00Z',
            'last_seen_before': '2024-01-01T00:00:00Z'
        }, queryset=MISPAttribute.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), attr1) 