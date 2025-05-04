from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework import status

from api.core.responses import success_response, error_response
from api.core.utils import get_tenant_from_request
from notifications.models import NotificationChannel
from notifications.permissions import ManageNotificationsPermission
from notifications.serializers import (
    NotificationChannelSerializer,
    EmailChannelSerializer,
    SlackChannelSerializer,
    MattermostChannelSerializer,
    WebhookChannelSerializer,
    SMSChannelSerializer
)

import logging

logger = logging.getLogger('api.notifications')

class NotificationChannelCreateView(CreateAPIView):
    """
    Create a new notification channel.
    """
    permission_classes = [IsAuthenticated, ManageNotificationsPermission]
    serializer_class = NotificationChannelSerializer
    
    @extend_schema(
        tags=['Notification System'],
        summary="Create notification channel",
        description="Create a new notification channel for delivering notifications.",
        request=NotificationChannelSerializer,
        responses={201: NotificationChannelSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new notification channel.
        """
        return self.create(request, *args, **kwargs)
    
    def get_serializer_class(self):
        """
        Return different serializers based on channel type.
        """
        channel_type = self.request.data.get('channel_type')
        
        if channel_type == 'email':
            return EmailChannelSerializer
        elif channel_type == 'slack':
            return SlackChannelSerializer
        elif channel_type == 'mattermost':
            return MattermostChannelSerializer
        elif channel_type == 'webhook':
            return WebhookChannelSerializer
        elif channel_type == 'sms':
            return SMSChannelSerializer
            
        # Default to base serializer
        return NotificationChannelSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Custom create to handle tenant assignment.
        """
        try:
            tenant = get_tenant_from_request(request)
            
            # Add tenant to the data
            data = request.data.copy()
            data['company'] = tenant.id
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return success_response(
                data=serializer.data,
                message=f"{data.get('channel_type', 'Notification').capitalize()} channel created successfully",
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error creating notification channel: {str(e)}")
            return error_response(
                message=f"Error creating notification channel: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            ) 