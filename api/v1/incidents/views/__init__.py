from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from incidents.models import Incident
from ..serializers import (
    IncidentSerializer,
    IncidentDetailSerializer,
    IncidentCreateSerializer,
    IncidentUpdateSerializer
)
from ..filters import IncidentFilter
from ..permissions import IncidentPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.throttling import AdminRateThrottle, StandardUserRateThrottle
from api.core.viewsets import StandardViewSet
from api.core.audit import AuditLogMixin
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .incident_create import IncidentCreateMixin
from .incident_detail import IncidentDetailMixin
from .incident_custom_actions import IncidentCustomActionsMixin


@extend_schema(tags=['Incident Management'])
class IncidentViewSet(AuditLogMixin, IncidentCreateMixin, IncidentDetailMixin, IncidentCustomActionsMixin, StandardViewSet):
    """
    API endpoint for incident management.
    
    Incidents represent security events that require investigation and response.
    Each incident belongs to a specific company and can only be viewed by users of that company.
    """
    serializer_class = IncidentSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IncidentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = IncidentFilter
    search_fields = ['title', 'description', 'summary']
    ordering_fields = ['created_at', 'updated_at', 'severity', 'status', 'impact_score']
    ordering = ['-created_at']
    entity_type = 'incident'  # Define entity type for RBAC and audit logging
    
    # Success messages for standardized responses
    success_message_create = "Incident created successfully"
    success_message_update = "Incident updated successfully"
    success_message_delete = "Incident deleted successfully"
    
    def get_additional_log_data(self, request, obj=None, action=None):
        """
        Customize audit log data for incidents.
        
        Add incident-specific fields to the audit log, such as severity,
        status, and company information.
        
        Args:
            request: The HTTP request
            obj: The incident object being acted upon
            action: The action being performed (create, update, delete)
            
        Returns:
            dict: Additional data for the audit log
        """
        # Get standard log data from parent class
        data = super().get_additional_log_data(request, obj, action)
        
        # Add incident-specific data
        if obj:
            data.update({
                'incident_severity': getattr(obj, 'severity', None),
                'incident_status': getattr(obj, 'status', None),
                'incident_title': getattr(obj, 'title', None),
                'company_id': str(obj.company.id) if getattr(obj, 'company', None) else None,
                'company_name': obj.company.name if getattr(obj, 'company', None) else None,
            })
            
        return data
    
    @extend_schema(
        summary="List all incidents with filtering and pagination",
        description="Returns a paginated list of incidents that the current user has permission to view.",
        parameters=[
            OpenApiParameter(name="severity", description="Filter by severity level", type=str, enum=["low", "medium", "high", "critical"]),
            OpenApiParameter(name="status", description="Filter by incident status", type=str, enum=["open", "in_progress", "resolved", "closed"]),
            OpenApiParameter(name="search", description="Search in title, description, and summary", type=str),
            OpenApiParameter(name="ordering", description="Order results by field", type=str, enum=["created_at", "-created_at", "severity", "-severity", "status", "-status"]),
        ],
        responses={200: IncidentSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Retrieve a specific incident",
        description="Returns detailed information about a specific incident, including related alerts and observables.",
        responses={200: IncidentDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create a new incident",
        description="Creates a new incident in the system.",
        request=IncidentCreateSerializer,
        responses={201: IncidentSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update an incident",
        description="Updates an existing incident.",
        request=IncidentUpdateSerializer,
        responses={200: IncidentSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Partially update an incident",
        description="Partially updates an existing incident.",
        request=IncidentUpdateSerializer,
        responses={200: IncidentSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete an incident",
        description="Deletes an incident from the system.",
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def get_serializer_class(self):
        """
        Returns the appropriate serializer based on the action.
        """
        if self.action == 'create':
            return IncidentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return IncidentUpdateSerializer
        elif self.action == 'retrieve':
            return IncidentDetailSerializer
        return IncidentSerializer
    
    def get_queryset(self):
        """
        Returns only incidents from the user's company, unless the user is a superuser.
        """
        # Handle schema generation
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return Incident.objects.none()
            
        user = self.request.user
        
        if user.is_superuser:
            return Incident.objects.all()
        
        return Incident.objects.filter(company=user.company)
    
    def get_throttles(self):
        """
        Defines throttling based on the user's role.
        """
        if self.request.user.is_superuser or self.request.user.role == 'admin_company':
            return [AdminRateThrottle()]
        return [StandardUserRateThrottle()]


__all__ = [
    'IncidentViewSet',
] 