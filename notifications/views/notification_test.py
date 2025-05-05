from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404

from notifications.models import NotificationChannel
from notifications.serializers import NotificationChannelSerializer
from notifications.serializers.test_serializers import NotificationTestSerializer
from notifications.permissions import ManageNotificationsPermission
from notifications.tasks import send_test_notification
from api.core.responses import success_response, error_response
from api.core.utils import get_tenant_from_request

import logging

logger = logging.getLogger('api.notifications')

class NotificationTestView(APIView):
    """
    API endpoint for testing notification channels.
    Sends a test message through the specified notification channel.
    """
    permission_classes = [ManageNotificationsPermission]
    
    @extend_schema(
        tags=['Notification System'],
        summary="Test a notification channel",
        description="Sends a test message through the specified notification channel to verify its configuration.",
        request=NotificationTestSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                    "data": {"type": "object"}
                }
            },
            404: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"}
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"}
                }
            }
        }
    )
    def post(self, request):
        """
        Send a test notification through the specified channel.
        """
        serializer = NotificationTestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid request data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        validated_data = serializer.validated_data
        tenant = get_tenant_from_request(request)
        channel_id = validated_data['channel_id']
        test_message = validated_data.get('message', 'This is a test notification from SentinelIQ.')
        
        try:
            # Get the channel and ensure it belongs to the current tenant
            channel = get_object_or_404(NotificationChannel, id=channel_id, company=tenant)
            
            # Log the test request
            logger.info(f"Test notification requested for channel {channel.name} by {request.user.email}")
            
            # Send the test notification asynchronously using Celery
            task = send_test_notification.delay(channel.id, test_message)
            
            return success_response(
                data={
                    "channel": NotificationChannelSerializer(channel).data,
                    "message": test_message,
                    "task_id": task.id,
                },
                message=f"Test notification sent to {channel.name} ({channel.get_channel_type_display()})"
            )
            
        except Exception as e:
            logger.error(f"Error testing notification channel: {str(e)}")
            return error_response(
                message=f"Error testing notification channel: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 