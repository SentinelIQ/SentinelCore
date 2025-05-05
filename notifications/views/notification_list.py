from django.db.models import Q
from rest_framework.mixins import ListModelMixin
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
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
        tags=['Notification System'],
        summary="List notifications",
        description=(
            "Retrieves a paginated list of notifications for the current user with filtering options. "
            "This endpoint powers the notification center across the SOAR platform, providing access to both "
            "personal notifications where the user is a direct recipient and company-wide notifications for "
            "the user's organization. The endpoint supports comprehensive filtering by category, priority, "
            "and notification scope, as well as text search capabilities. Results can be ordered by recency "
            "or priority to help users identify the most important notifications first. This notification feed "
            "is essential for security teams to stay informed about alerts, incidents, tasks, and system events."
        ),
        parameters=[
            OpenApiParameter(name='category', type=str, description='Filter by notification category (alert, incident, task, system, report)'),
            OpenApiParameter(name='priority', type=str, description='Filter by notification priority (low, medium, high, critical)'),
            OpenApiParameter(name='is_company_wide', type=bool, description='Filter for company-wide notifications only'),
            OpenApiParameter(name='search', type=str, description='Search in notification title and message'),
            OpenApiParameter(name='ordering', type=str, description='Order by field (created_at, priority). Prefix with - for descending order.'),
        ],
        responses={
            200: OpenApiResponse(
                response=NotificationLiteSerializer,
                description="Notifications retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="notification_list",
                        summary="List of notifications",
                        description="Example of a paginated list of notifications for the current user",
                        value={
                            "status": "success",
                            "message": "Notifications retrieved successfully",
                            "data": {
                                "count": 15,
                                "next": "http://api.example.com/api/v1/notifications/?page=2",
                                "previous": None,
                                "results": [
                                    {
                                        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                                        "title": "Critical Alert Detected",
                                        "message": "A critical security alert has been detected: Potential data exfiltration activity",
                                        "category": "alert",
                                        "priority": "critical",
                                        "is_company_wide": False,
                                        "created_at": "2023-05-15T14:30:45Z",
                                        "is_read": False,
                                        "data": {
                                            "alert_id": "a1b2c3d4",
                                            "link": "/alerts/a1b2c3d4"
                                        }
                                    },
                                    {
                                        "id": "3e7dea7a-b581-4d9e-82c2-b6b44476b3a7",
                                        "title": "New Incident Assigned",
                                        "message": "You have been assigned to incident INC-2023-05-15-001: Network Intrusion",
                                        "category": "incident",
                                        "priority": "high",
                                        "is_company_wide": False,
                                        "created_at": "2023-05-15T10:22:18Z",
                                        "is_read": True,
                                        "data": {
                                            "incident_id": "INC-2023-05-15-001",
                                            "link": "/incidents/INC-2023-05-15-001"
                                        }
                                    },
                                    {
                                        "id": "d5c59a2b-8dfb-4032-9c8c-110ac4b4c4aa",
                                        "title": "System Maintenance Scheduled",
                                        "message": "The system will undergo scheduled maintenance on May 20, 2023 from 02:00-04:00 UTC.",
                                        "category": "system",
                                        "priority": "medium",
                                        "is_company_wide": True,
                                        "created_at": "2023-05-14T08:15:30Z",
                                        "is_read": False,
                                        "data": {
                                            "maintenance_id": "MAINT-2023-05-20",
                                            "duration_hours": 2
                                        }
                                    }
                                ]
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied error",
                        description="Example of response when user lacks notification viewing permissions",
                        value={
                            "status": "error",
                            "message": "You do not have permission to view notifications",
                            "data": None
                        }
                    )
                ]
            )
        }
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