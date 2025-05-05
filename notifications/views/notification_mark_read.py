from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
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
        tags=['Notification System'],
        summary="Mark notification as read",
        description=(
            "Marks a notification as read for the current user by updating the delivery status. "
            "This endpoint is critical for maintaining accurate user notification state across the SOAR platform. "
            "When a user acknowledges a notification through the UI, this endpoint updates all delivery statuses "
            "associated with the notification for that user and records the timestamp of when the notification was read. "
            "This information is used for notification analytics, user engagement tracking, and ensuring that "
            "important security alerts are acknowledged. The system automatically creates appropriate delivery "
            "status records if they don't exist."
        ),
        responses={
            200: OpenApiResponse(
                description="Notification marked as read successfully",
                examples=[
                    OpenApiExample(
                        name="mark_read_success",
                        summary="Notification marked as read",
                        description="Example of a successful notification mark as read response",
                        value={
                            "status": "success",
                            "message": "Notification marked as read",
                            "data": None
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Notification not found",
                examples=[
                    OpenApiExample(
                        name="notification_not_found",
                        summary="Notification not found error",
                        description="Example of response when the specified notification doesn't exist",
                        value={
                            "status": "error",
                            "message": "Notification not found",
                            "data": None
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
                        description="Example of response when user tries to mark someone else's notification as read",
                        value={
                            "status": "error",
                            "message": "You do not have permission to mark this notification as read",
                            "data": None
                        }
                    )
                ]
            )
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