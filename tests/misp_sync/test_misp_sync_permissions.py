from django.test import TestCase, RequestFactory
from rest_framework.test import APITestCase, APIRequestFactory
from misp_sync.models import MISPEvent, MISPObject, MISPAttribute
from misp_sync.permissions import (
    HasMISPEventPermission,
    HasMISPObjectPermission,
    HasMISPAttributePermission
)
from api.core.test_utils import APITestCaseMixin
from api.core.permissions import IsSuperUser, IsAdminCompany, IsAnalystCompany, IsCompanyMember

class MISPSyncPermissionTests(APITestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.setup_tenant()
        self.setup_user()
        self.setup_company()
        self.setup_company_member()
        self.setup_company_analyst()
        self.setup_company_admin()
        self.setup_superuser()
        self.factory = APIRequestFactory()

    def test_misp_event_permissions(self):
        """Test MISP event permissions"""
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

        # Test superuser permissions
        request = self.factory.get('/')
        request.user = self.superuser
        permission = HasMISPEventPermission()
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, event))

        # Test company admin permissions
        request.user = self.company_admin
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, event))

        # Test company analyst permissions
        request.user = self.company_analyst
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, event))

        # Test company member permissions
        request.user = self.company_member
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, event))

        # Test unauthorized user permissions
        request.user = self.user
        self.assertFalse(permission.has_permission(request, None))
        self.assertFalse(permission.has_object_permission(request, None, event))

    def test_misp_object_permissions(self):
        """Test MISP object permissions"""
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

        # Test superuser permissions
        request = self.factory.get('/')
        request.user = self.superuser
        permission = HasMISPObjectPermission()
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, obj))

        # Test company admin permissions
        request.user = self.company_admin
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, obj))

        # Test company analyst permissions
        request.user = self.company_analyst
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, obj))

        # Test company member permissions
        request.user = self.company_member
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, obj))

        # Test unauthorized user permissions
        request.user = self.user
        self.assertFalse(permission.has_permission(request, None))
        self.assertFalse(permission.has_object_permission(request, None, obj))

    def test_misp_attribute_permissions(self):
        """Test MISP attribute permissions"""
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

        # Test superuser permissions
        request = self.factory.get('/')
        request.user = self.superuser
        permission = HasMISPAttributePermission()
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, attr))

        # Test company admin permissions
        request.user = self.company_admin
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, attr))

        # Test company analyst permissions
        request.user = self.company_analyst
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, attr))

        # Test company member permissions
        request.user = self.company_member
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, attr))

        # Test unauthorized user permissions
        request.user = self.user
        self.assertFalse(permission.has_permission(request, None))
        self.assertFalse(permission.has_object_permission(request, None, attr))

    def test_misp_event_cross_company_permissions(self):
        """Test MISP event permissions across different companies"""
        other_company = self.create_company(name="Other Company")
        other_company_admin = self.create_company_admin(other_company)

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

        request = self.factory.get('/')
        request.user = other_company_admin
        permission = HasMISPEventPermission()
        self.assertTrue(permission.has_permission(request, None))
        self.assertFalse(permission.has_object_permission(request, None, event))

    def test_misp_object_cross_company_permissions(self):
        """Test MISP object permissions across different companies"""
        other_company = self.create_company(name="Other Company")
        other_company_admin = self.create_company_admin(other_company)

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

        request = self.factory.get('/')
        request.user = other_company_admin
        permission = HasMISPObjectPermission()
        self.assertTrue(permission.has_permission(request, None))
        self.assertFalse(permission.has_object_permission(request, None, obj))

    def test_misp_attribute_cross_company_permissions(self):
        """Test MISP attribute permissions across different companies"""
        other_company = self.create_company(name="Other Company")
        other_company_admin = self.create_company_admin(other_company)

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

        request = self.factory.get('/')
        request.user = other_company_admin
        permission = HasMISPAttributePermission()
        self.assertTrue(permission.has_permission(request, None))
        self.assertFalse(permission.has_object_permission(request, None, attr)) 