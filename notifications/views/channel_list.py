from rest_framework.mixins import ListModelMixin
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from notifications.models import NotificationChannel
from notifications.serializers import NotificationChannelLiteSerializer
from notifications.permissions import ManageNotificationsPermission
from api.core.utils import get_tenant_from_request
from api.core.responses import StandardResponse

class NotificationChannelListView(ListModelMixin):
    """
    View for listing notification channels with filtering options.
    Only users with manage_notifications permission can access this view.
    """
    serializer_class = NotificationChannelLiteSerializer
    permission_classes = [ManageNotificationsPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['channel_type', 'is_enabled']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @extend_schema(
        tags=['Notification System'],
        summary="List notification channels",
        description="Returns a list of notification channels for the current company. "
                    "Requires manage_notifications permission.",
        parameters=[
            OpenApiParameter(name='channel_type', type=str, description='Filter by channel type (email, slack, webhook, in_app, sms)'),
            OpenApiParameter(name='is_enabled', type=bool, description='Filter by enabled status'),
            OpenApiParameter(name='search', type=str, description='Search in channel name'),
            OpenApiParameter(name='ordering', type=str, description='Order by field (name, created_at). Prefix with - for descending order.'),
        ],
        responses={200: NotificationChannelLiteSerializer}
    )
    def list(self, request, *args, **kwargs):
        """List notification channels for the current company"""
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """Get notification channels for the current company"""
        company = get_tenant_from_request(self.request)
        return NotificationChannel.objects.filter(company=company) 