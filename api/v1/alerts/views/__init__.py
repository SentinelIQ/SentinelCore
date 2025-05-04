from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from alerts.models import Alert
from ..serializers import (
    AlertSerializer,
    AlertDetailSerializer,
    AlertCreateSerializer,
    AlertUpdateSerializer
)
from ..filters import AlertFilter
from ..permissions import AlertPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.throttling import AdminRateThrottle, StandardUserRateThrottle
from api.core.viewsets import StandardViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .alert_create import AlertCreateMixin
from .alert_detail import AlertDetailMixin
from .alert_custom_actions import AlertCustomActionsMixin


@extend_schema(tags=['Alert Management'])
class AlertViewSet(AlertCreateMixin, AlertDetailMixin, AlertCustomActionsMixin, StandardViewSet):
    """
    API endpoint for alert management.
    
    Alerts represent security notifications that can be escalated to incidents.
    Each alert belongs to a specific company and can only be viewed by users of that company.
    """
    serializer_class = AlertSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AlertPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AlertFilter
    search_fields = ['title', 'description', 'source']
    ordering_fields = ['created_at', 'updated_at', 'severity', 'status']
    ordering = ['-created_at']
    entity_type = 'alert'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Alert created successfully"
    success_message_update = "Alert updated successfully"
    success_message_delete = "Alert deleted successfully"
    
    @extend_schema(
        summary="List all alerts with filtering and pagination",
        description="Returns a paginated list of alerts that the current user has permission to view.",
        parameters=[
            OpenApiParameter(name="severity", description="Filter by severity level", type=str, enum=["low", "medium", "high", "critical"]),
            OpenApiParameter(name="status", description="Filter by alert status", type=str, enum=["new", "in_progress", "resolved", "escalated"]),
            OpenApiParameter(name="search", description="Search in title, description, and source", type=str),
            OpenApiParameter(name="ordering", description="Order results by field", type=str, enum=["created_at", "-created_at", "severity", "-severity", "status", "-status"]),
        ],
        responses={200: AlertSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Retrieve a specific alert",
        description="Returns detailed information about a specific alert, including related observables.",
        responses={200: AlertDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create a new alert",
        description="Creates a new alert in the system.",
        request=AlertCreateSerializer,
        responses={201: AlertSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update an alert",
        description="Updates an existing alert. Cannot change status to 'escalated' directly.",
        request=AlertUpdateSerializer,
        responses={200: AlertSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Partially update an alert",
        description="Partially updates an existing alert. Cannot change status to 'escalated' directly.",
        request=AlertUpdateSerializer,
        responses={200: AlertSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete an alert",
        description="Deletes an alert from the system.",
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def get_serializer_class(self):
        """
        Returns the appropriate serializer based on the action.
        """
        if self.action == 'create':
            return AlertCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AlertUpdateSerializer
        elif self.action == 'retrieve':
            return AlertDetailSerializer
        return AlertSerializer
    
    def get_queryset(self):
        """
        Returns only alerts from the user's company, unless the user is a superuser.
        """
        user = self.request.user
        
        if user.is_superuser:
            return Alert.objects.all()
        
        return Alert.objects.filter(company=user.company)
    
    def get_throttles(self):
        """
        Defines throttling based on the user's role.
        """
        if self.request.user.is_superuser or self.request.user.role == 'admin_company':
            return [AdminRateThrottle()]
        return [StandardUserRateThrottle()]


__all__ = [
    'AlertViewSet',
] 