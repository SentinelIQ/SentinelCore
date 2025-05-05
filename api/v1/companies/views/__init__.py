from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from companies.models import Company
from ..serializers import (
    CompanySerializer,
    CompanyDetailSerializer,
    CompanyCreateSerializer
)
from ..filters import CompanyFilter
from ..permissions import CompanyPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.throttling import AdminRateThrottle
from api.core.viewsets import StandardViewSet
from api.core.audit import AuditLogMixin
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

from .company_create import CompanyCreateMixin
from .company_detail import CompanyDetailMixin
from .company_custom_actions import CompanyCustomActionsMixin


@extend_schema_view(
    list=extend_schema(
        summary="List all companies",
        description="Get a paginated list of companies the user has access to. Superusers see all companies, while regular users only see their own."
    ),
    retrieve=extend_schema(
        summary="Get company details",
        description="Retrieve detailed information about a specific company, including associated users."
    ),
    create=extend_schema(
        summary="Create company with admin",
        description="Creates a new company and an associated admin user. Only superadmins can perform this action.",
        examples=[
            OpenApiExample(
                name="Create Example",
                value={
                    "name": "Example Company",
                    "admin_user": {
                        "username": "admin_company",
                        "email": "admin@company.com",
                        "password": "secure_password",
                        "first_name": "Admin",
                        "last_name": "Company"
                    }
                },
                request_only=True,
            )
        ]
    ),
    update=extend_schema(
        summary="Update a company",
        description="Update all fields of an existing company. Only accessible to superusers."
    ),
    partial_update=extend_schema(
        summary="Partially update a company",
        description="Update specific fields of an existing company. Only accessible to superusers."
    ),
    destroy=extend_schema(
        summary="Delete a company",
        description="Permanently delete a company and all associated data. Only accessible to superusers."
    )
)
@extend_schema(tags=['Company Management'])
class CompanyViewSet(
    AuditLogMixin,
    CompanyCreateMixin,
    CompanyDetailMixin,
    CompanyCustomActionsMixin,
    StandardViewSet
):
    """
    API endpoint for company management.
    
    Companies are the top-level tenant entities in the system.
    Each company has its own users, alerts, and incidents.
    """
    serializer_class = CompanySerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [CompanyPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CompanyFilter
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    throttle_classes = [AdminRateThrottle]
    entity_type = 'company'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Company created successfully"
    success_message_update = "Company updated successfully"
    success_message_delete = "Company deleted successfully"
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        
        Returns:
            Serializer class appropriate for the current action
        """
        if self.action == 'create':
            return CompanyCreateSerializer
        elif self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanySerializer
    
    def get_queryset(self):
        """
        Filter companies based on user permissions:
        - Superusers can see all companies
        - Regular users can only see their own company
        """
        user = self.request.user
        queryset = Company.objects.all()
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return Company.objects.none()  # Return empty queryset if not authenticated
        
        # Superuser sees all companies
        if user.is_superuser:
            return queryset
        
        # Regular user sees only their own company
        if hasattr(user, 'company') and user.company:
            return queryset.filter(id=user.company.id)
        
        # If no company, sees nothing
        return Company.objects.none()

    def get_additional_log_data(self, request, obj=None, action=None):
        """
        Customize audit log data for companies.
        
        Add company-specific fields to the audit log.
        
        Args:
            request: The HTTP request
            obj: The company object being acted upon
            action: The action being performed (create, update, delete)
            
        Returns:
            dict: Additional data for the audit log
        """
        # Get standard log data from parent class
        data = super().get_additional_log_data(request, obj, action)
        
        # Add company-specific data
        if obj:
            data.update({
                'company_name': getattr(obj, 'name', None),
                'user_count': obj.users.count() if hasattr(obj, 'users') else 0,
            })
            
        return data


__all__ = [
    'CompanyViewSet',
]
