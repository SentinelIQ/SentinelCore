from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from misp_sync.admin import (
    MISPEventAdmin,
    MISPObjectAdmin,
    MISPAttributeAdmin
)
from misp_sync.models import MISPEvent, MISPObject, MISPAttribute
from api.core.test_utils import APITestCaseMixin

class MockRequest:
    pass

class MockSuperUser:
    def has_perm(self, perm):
        return True

class MISPSyncAdminTests(APITestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.setup_tenant()
        self.setup_user()
        self.setup_company()
        self.setup_company_member()
        self.setup_company_analyst()
        self.setup_company_admin()
        self.setup_superuser()

        self.site = AdminSite()
        self.request = MockRequest()
        self.request.user = MockSuperUser()

        self.event_admin = MISPEventAdmin(MISPEvent, self.site)
        self.object_admin = MISPObjectAdmin(MISPObject, self.site)
        self.attribute_admin = MISPAttributeAdmin(MISPAttribute, self.site)

    def test_misp_event_admin(self):
        """Test MISP event admin configuration"""
        # Test list_display
        self.assertEqual(
            self.event_admin.list_display,
            ('event_id', 'info', 'threat_level_id', 'date', 'published', 'company')
        )

        # Test list_filter
        self.assertEqual(
            self.event_admin.list_filter,
            ('threat_level_id', 'published', 'date', 'company')
        )

        # Test search_fields
        self.assertEqual(
            self.event_admin.search_fields,
            ('info', 'uuid', 'event_id')
        )

        # Test readonly_fields
        self.assertEqual(
            self.event_admin.readonly_fields,
            ('event_id', 'uuid', 'timestamp', 'created_at', 'updated_at')
        )

        # Test filter_horizontal
        self.assertEqual(
            self.event_admin.filter_horizontal,
            ('objects', 'attributes')
        )

    def test_misp_object_admin(self):
        """Test MISP object admin configuration"""
        # Test list_display
        self.assertEqual(
            self.object_admin.list_display,
            ('object_id', 'name', 'meta_category', 'event', 'deleted', 'company')
        )

        # Test list_filter
        self.assertEqual(
            self.object_admin.list_filter,
            ('meta_category', 'deleted', 'company')
        )

        # Test search_fields
        self.assertEqual(
            self.object_admin.search_fields,
            ('name', 'uuid', 'object_id', 'description')
        )

        # Test readonly_fields
        self.assertEqual(
            self.object_admin.readonly_fields,
            ('object_id', 'uuid', 'timestamp', 'created_at', 'updated_at')
        )

    def test_misp_attribute_admin(self):
        """Test MISP attribute admin configuration"""
        # Test list_display
        self.assertEqual(
            self.attribute_admin.list_display,
            ('attribute_id', 'type', 'category', 'value', 'to_ids', 'event', 'deleted', 'company')
        )

        # Test list_filter
        self.assertEqual(
            self.attribute_admin.list_filter,
            ('type', 'category', 'to_ids', 'deleted', 'company')
        )

        # Test search_fields
        self.assertEqual(
            self.attribute_admin.search_fields,
            ('uuid', 'attribute_id', 'value', 'comment')
        )

        # Test readonly_fields
        self.assertEqual(
            self.attribute_admin.readonly_fields,
            ('attribute_id', 'uuid', 'timestamp', 'created_at', 'updated_at')
        )

    def test_misp_event_admin_actions(self):
        """Test MISP event admin actions"""
        # Create test event
        event = MISPEvent.objects.create(
            event_id=1,
            info="Test Event",
            threat_level_id=1,
            analysis=0,
            date="2024-01-01",
            published=False,
            uuid="test-uuid",
            timestamp=1234567890,
            distribution=0,
            sharing_group_id=0,
            org_id=1,
            orgc_id=1,
            attribute_count=0,
            company=self.company
        )

        # Test publish action
        self.event_admin.publish_events(self.request, MISPEvent.objects.filter(id=event.id))
        event.refresh_from_db()
        self.assertTrue(event.published)

        # Test unpublish action
        self.event_admin.unpublish_events(self.request, MISPEvent.objects.filter(id=event.id))
        event.refresh_from_db()
        self.assertFalse(event.published)

    def test_misp_object_admin_actions(self):
        """Test MISP object admin actions"""
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

        # Create test object
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

        # Test soft delete action
        self.object_admin.soft_delete_objects(self.request, MISPObject.objects.filter(id=obj.id))
        obj.refresh_from_db()
        self.assertTrue(obj.deleted)

        # Test restore action
        self.object_admin.restore_objects(self.request, MISPObject.objects.filter(id=obj.id))
        obj.refresh_from_db()
        self.assertFalse(obj.deleted)

    def test_misp_attribute_admin_actions(self):
        """Test MISP attribute admin actions"""
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

        # Create test attribute
        attr = MISPAttribute.objects.create(
            attribute_id=1,
            type="ip-src",
            category="Network activity",
            to_ids=False,
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

        # Test enable_ids action
        self.attribute_admin.enable_ids(self.request, MISPAttribute.objects.filter(id=attr.id))
        attr.refresh_from_db()
        self.assertTrue(attr.to_ids)

        # Test disable_ids action
        self.attribute_admin.disable_ids(self.request, MISPAttribute.objects.filter(id=attr.id))
        attr.refresh_from_db()
        self.assertFalse(attr.to_ids)

        # Test soft delete action
        self.attribute_admin.soft_delete_attributes(self.request, MISPAttribute.objects.filter(id=attr.id))
        attr.refresh_from_db()
        self.assertTrue(attr.deleted)

        # Test restore action
        self.attribute_admin.restore_attributes(self.request, MISPAttribute.objects.filter(id=attr.id))
        attr.refresh_from_db()
        self.assertFalse(attr.deleted) 