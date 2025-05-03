from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from notifications.models import Notification, NotificationDeliveryStatus
from notifications.permissions import ViewOwnNotificationsPermission
from api.core.responses import success_response

class NotificationMarkReadView:
    """
    View mixin for marking notifications as read.
    Users can mark their own notifications as read.
    """
    permission_classes = [ViewOwnNotificationsPermission]
    
    @extend_schema(
        tags=['Notifications'],
        summary="Mark notification as read",
        description="Marks a notification as read for the current user by updating "
                    "the delivery status. Users can only mark their own notifications.",
        responses={
            200: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}},
            404: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}
        }
    )
    @action(methods=['post'], detail=True, url_path='mark-read')
    def mark_read(self, request, id=None, *args, **kwargs):
        """Mark a notification as read by updating the delivery status"""
        notification = self.get_object()
        user = request.user
        
        # Find all delivery statuses for this notification and user
        delivery_statuses = NotificationDeliveryStatus.objects.filter(
            notification=notification,
            recipient=user
        )
        
        # If no delivery status exists, create for in-app at minimum
        if not delivery_statuses.exists():
            # Get or create an in-app channel for the company
            from notifications.models import NotificationChannel
            in_app_channel, _ = NotificationChannel.objects.get_or_create(
                company=user.company,
                channel_type='in_app',
                defaults={'name': 'In-App Notifications'}
            )
            
            # Create a delivery status for the in-app channel
            delivery_status = NotificationDeliveryStatus.objects.create(
                notification=notification,
                channel=in_app_channel,
                recipient=user,
                status='delivered',
                delivered_at=timezone.now()
            )
        else:
            # Update all delivery statuses to mark as read
            delivery_statuses.update(
                read_at=timezone.now()
            )
        
        # Use success_response instead of StandardResponse with a separate status parameter
        return success_response(
            message="Notification marked as read"
        ) 