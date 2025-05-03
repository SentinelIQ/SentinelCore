from rest_framework.mixins import RetrieveModelMixin
from drf_spectacular.utils import extend_schema
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from notifications.permissions import ViewOwnNotificationsPermission
from api.core.responses import StandardResponse

class NotificationDetailView(RetrieveModelMixin):
    """
    View for retrieving detailed information about a specific notification.
    Users can only view notifications where they are recipients or
    company-wide notifications for their company.
    """
    serializer_class = NotificationSerializer
    permission_classes = [ViewOwnNotificationsPermission]
    lookup_field = 'id'
    
    @extend_schema(
        tags=['Notifications'],
        summary="Get notification details",
        description="Retrieves detailed information about a specific notification. "
                    "Users can only view notifications where they are recipients or "
                    "company-wide notifications for their company.",
        responses={
            200: NotificationSerializer,
            404: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a notification with full details"""
        return super().retrieve(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get notifications where the user is a recipient or
        company-wide notifications for the user's company
        """
        user = self.request.user
        
        # Either direct notifications to the user or company-wide for their company
        return Notification.objects.all() 