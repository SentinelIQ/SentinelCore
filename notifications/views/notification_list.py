from django.db.models import Q
from rest_framework.mixins import ListModelMixin
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from notifications.models import Notification
from notifications.serializers import NotificationLiteSerializer
from notifications.permissions import ViewOwnNotificationsPermission
from api.core.responses import StandardResponse

class NotificationListView(ListModelMixin):
    """
    View for listing notifications with filtering options.
    Users can see notifications where they are recipients or
    company-wide notifications for their company.
    """
    serializer_class = NotificationLiteSerializer
    permission_classes = [ViewOwnNotificationsPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'priority', 'is_company_wide']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    
    @extend_schema(
        tags=['Notifications'],
        summary="List notifications",
        description="Returns a list of notifications for the current user. This includes "
                    "notifications where the user is a direct recipient and company-wide "
                    "notifications for the user's company.",
        parameters=[
            OpenApiParameter(name='category', type=str, description='Filter by notification category (alert, incident, task, system, report)'),
            OpenApiParameter(name='priority', type=str, description='Filter by notification priority (low, medium, high, critical)'),
            OpenApiParameter(name='is_company_wide', type=bool, description='Filter for company-wide notifications only'),
            OpenApiParameter(name='search', type=str, description='Search in notification title and message'),
            OpenApiParameter(name='ordering', type=str, description='Order by field (created_at, priority). Prefix with - for descending order.'),
        ],
        responses={200: NotificationLiteSerializer}
    )
    def list(self, request, *args, **kwargs):
        """List notifications for the current user with filtering options"""
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get notifications where the user is a recipient or
        company-wide notifications for the user's company
        """
        user = self.request.user
        
        # Either direct notifications to the user or company-wide for their company
        queryset = Notification.objects.filter(
            Q(recipients=user) | 
            Q(is_company_wide=True, company=user.company)
        ).distinct()
        
        return queryset 