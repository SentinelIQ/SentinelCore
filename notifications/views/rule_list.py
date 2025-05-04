from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response, error_response
from api.core.utils import get_tenant_from_request
from notifications.models import NotificationRule
from notifications.permissions import ManageNotificationsPermission
from notifications.serializers import NotificationRuleSerializer

import logging

logger = logging.getLogger('api.notifications')

class NotificationRuleListView(ListAPIView):
    """
    List notification rules for the current tenant.
    """
    permission_classes = [IsAuthenticated, ManageNotificationsPermission]
    serializer_class = NotificationRuleSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'event_type', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    @extend_schema(
        tags=['Notification System'],
        summary="List notification rules",
        description="Returns a paginated list of notification rules for the current tenant, with optional filtering.",
        parameters=[
            OpenApiParameter(name='event_type', description='Filter by event type', required=False),
            OpenApiParameter(name='is_active', description='Filter by active status', required=False),
            OpenApiParameter(name='search', description='Search by name or description', required=False),
            OpenApiParameter(name='ordering', description='Order by field (prefix with - for descending)', required=False),
        ],
        responses={200: NotificationRuleSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """
        List notification rules for the current tenant with optional filtering.
        """
        try:
            tenant = get_tenant_from_request(request)
            self.queryset = NotificationRule.objects.filter(company=tenant)
            
            response = super().list(request, *args, **kwargs)
            return success_response(
                data=response.data,
                message="Notification rules retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error listing notification rules: {str(e)}")
            return error_response(message=f"Error retrieving notification rules: {str(e)}") 