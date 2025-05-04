from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404

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

class NotificationChannelDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a notification channel.
    """
    permission_classes = [IsAuthenticated, ManageNotificationsPermission]
    serializer_class = NotificationChannelSerializer
    
    def get_serializer_class(self):
        """
        Return different serializers based on channel type.
        """
        # For GET requests, determine serializer based on the object's channel_type
        if self.request.method == 'GET' and hasattr(self, 'object'):
            channel_type = self.object.channel_type
        # For PUT/PATCH requests, use the channel_type from the request data
        elif self.request.method in ['PUT', 'PATCH']:
            # If updating and channel_type is provided in the request
            channel_type = self.request.data.get('channel_type')
            if not channel_type and hasattr(self, 'object'):
                # If not provided in request, use the object's channel_type
                channel_type = self.object.channel_type
        else:
            # Default behavior for other methods or if we can't determine channel_type
            return NotificationChannelSerializer
            
        # Return appropriate serializer based on channel_type
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
    
    @extend_schema(
        tags=['Notification System'],
        summary="Get notification channel details",
        description="Retrieves details of a specific notification channel.",
        responses={200: NotificationChannelSerializer}
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a specific notification channel.
        """
        self.object = self.get_object()
        return self.retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Notification System'],
        summary="Update notification channel",
        description="Update an existing notification channel.",
        request=NotificationChannelSerializer,
        responses={200: NotificationChannelSerializer}
    )
    def put(self, request, *args, **kwargs):
        """
        Update a notification channel completely.
        """
        self.object = self.get_object()
        return self.update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Notification System'],
        summary="Partially update notification channel",
        description="Partially update an existing notification channel.",
        request=NotificationChannelSerializer,
        responses={200: NotificationChannelSerializer}
    )
    def patch(self, request, *args, **kwargs):
        """
        Update a notification channel partially.
        """
        self.object = self.get_object()
        return self.partial_update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Notification System'],
        summary="Delete notification channel",
        description="Delete an existing notification channel.",
        responses={204: None}
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a notification channel.
        """
        return self.destroy(request, *args, **kwargs)
    
    def get_object(self):
        """
        Get the notification channel and check tenant ownership.
        """
        tenant = get_tenant_from_request(self.request)
        channel_id = self.kwargs.get('pk')
        
        channel = get_object_or_404(
            NotificationChannel,
            id=channel_id,
            company=tenant
        )
        
        self.object = channel
        return channel
    
    def retrieve(self, request, *args, **kwargs):
        """
        Custom retrieve to use standard response format.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            # Get channel type for custom message
            channel_type = instance.get_channel_type_display()
            
            return success_response(
                data=serializer.data,
                message=f"{channel_type} channel retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving notification channel: {str(e)}")
            return error_response(message=f"Error retrieving notification channel: {str(e)}")
    
    def update(self, request, *args, **kwargs):
        """
        Custom update to use standard response format.
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            # Don't allow changing the channel type
            if 'channel_type' in request.data and request.data['channel_type'] != instance.channel_type:
                return error_response(
                    message="Cannot change the channel type. Create a new channel instead.",
                    status_code=400
                )
                
            data = request.data.copy()
            data['company'] = instance.company.id
            
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # Get channel type for custom message
            channel_type = instance.get_channel_type_display()
            
            return success_response(
                data=serializer.data,
                message=f"{channel_type} channel updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error updating notification channel: {str(e)}")
            return error_response(message=f"Error updating notification channel: {str(e)}")
    
    def destroy(self, request, *args, **kwargs):
        """
        Custom destroy to use standard response format.
        """
        try:
            instance = self.get_object()
            
            # Store name and type for response message
            channel_type = instance.get_channel_type_display()
            channel_name = instance.name
            
            self.perform_destroy(instance)
            
            return success_response(
                data=None,
                message=f"{channel_type} channel '{channel_name}' deleted successfully"
            )
            
        except Exception as e:
            logger.error(f"Error deleting notification channel: {str(e)}")
            return error_response(message=f"Error deleting notification channel: {str(e)}") 