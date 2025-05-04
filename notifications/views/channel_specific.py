from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework import status

from api.core.responses import success_response, error_response
from api.core.utils import get_tenant_from_request
from notifications.models import NotificationChannel
from notifications.permissions import ManageNotificationsPermission
from notifications.serializers import (
    EmailChannelSerializer,
    SlackChannelSerializer,
    MattermostChannelSerializer,
    WebhookChannelSerializer,
    SMSChannelSerializer
)

import logging

logger = logging.getLogger('api.notifications')

class BaseChannelCreateView(CreateAPIView):
    """
    Base view for creating a specific notification channel type.
    """
    permission_classes = [IsAuthenticated, ManageNotificationsPermission]
    channel_type = None  # Override in subclasses
    channel_display_name = None  # Override in subclasses
    
    def create(self, request, *args, **kwargs):
        """
        Custom create to handle tenant assignment and channel type.
        """
        try:
            # Add tenant and channel_type to the data
            data = request.data.copy()
            
            # Set company ID - try from tenant, fallback to user's company
            tenant = get_tenant_from_request(request)
            if tenant:
                data['company'] = tenant.id
            elif request.user and hasattr(request.user, 'company') and request.user.company:
                data['company'] = request.user.company.id
            else:
                return error_response(
                    message="Company ID is required and could not be inferred",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
            data['channel_type'] = self.channel_type
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return success_response(
                data=serializer.data,
                message=f"{self.channel_display_name} channel created successfully",
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error creating {self.channel_display_name} channel: {str(e)}")
            return error_response(
                message=f"Error creating {self.channel_display_name} channel: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class EmailChannelCreateView(BaseChannelCreateView):
    """
    Create a new email notification channel.
    """
    serializer_class = EmailChannelSerializer
    channel_type = 'email'
    channel_display_name = 'Email'
    
    @extend_schema(
        tags=['Notification System'],
        summary="Create email channel",
        description="""
        Create a new email notification channel with SMTP configuration.
        
        Required configuration fields:
        - smtp_host: SMTP server hostname
        - smtp_port: SMTP server port
        - smtp_username: SMTP server username
        - smtp_password: SMTP server password
        - from_email: Email address to send from
        
        Optional configuration fields:
        - use_tls: Whether to use TLS (default: true)
        - use_ssl: Whether to use SSL (default: false)
        """,
        request=EmailChannelSerializer,
        responses={201: EmailChannelSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new email notification channel.
        """
        return super().create(request, *args, **kwargs)


class SlackChannelCreateView(BaseChannelCreateView):
    """
    Create a new Slack notification channel.
    """
    serializer_class = SlackChannelSerializer
    channel_type = 'slack'
    channel_display_name = 'Slack'
    
    @extend_schema(
        tags=['Notification System'],
        summary="Create Slack channel",
        description="""
        Create a new Slack notification channel with webhook configuration.
        
        Required configuration fields:
        - webhook_url: Slack incoming webhook URL
        
        Optional configuration fields:
        - username: Bot username in Slack
        - icon_emoji: Emoji to use as the bot icon (e.g., ":robot_face:")
        - default_channel: Default Slack channel to post to
        """,
        request=SlackChannelSerializer,
        responses={201: SlackChannelSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new Slack notification channel.
        """
        return super().create(request, *args, **kwargs)


class MattermostChannelCreateView(BaseChannelCreateView):
    """
    Create a new Mattermost notification channel.
    """
    serializer_class = MattermostChannelSerializer
    channel_type = 'mattermost'
    channel_display_name = 'Mattermost'
    
    @extend_schema(
        tags=['Notification System'],
        summary="Create Mattermost channel",
        description="""
        Create a new Mattermost notification channel with webhook configuration.
        
        Required configuration fields:
        - webhook_url: Mattermost incoming webhook URL
        
        Optional configuration fields:
        - username: Bot username in Mattermost
        - channel: Mattermost channel to post to
        - icon_url: URL to an image to use as the bot icon
        - include_actions: Whether to include action buttons in notifications (default: true)
        - app_base_url: Base URL of the app for action links
        """,
        request=MattermostChannelSerializer,
        responses={201: MattermostChannelSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new Mattermost notification channel.
        """
        return super().create(request, *args, **kwargs)


class WebhookChannelCreateView(BaseChannelCreateView):
    """
    Create a new webhook notification channel.
    """
    serializer_class = WebhookChannelSerializer
    channel_type = 'webhook'
    channel_display_name = 'Webhook'
    
    @extend_schema(
        tags=['Notification System'],
        summary="Create webhook channel",
        description="""
        Create a new webhook notification channel.
        
        Required configuration fields:
        - url: Webhook URL to send notifications to
        
        Optional configuration fields:
        - headers: Dictionary of HTTP headers to include in requests
        - include_company: Whether to include company information in the payload (default: false)
        - method: HTTP method to use (default: "POST")
        """,
        request=WebhookChannelSerializer,
        responses={201: WebhookChannelSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new webhook notification channel.
        """
        return super().create(request, *args, **kwargs)


class SMSChannelCreateView(BaseChannelCreateView):
    """
    Create a new SMS notification channel.
    """
    serializer_class = SMSChannelSerializer
    channel_type = 'sms'
    channel_display_name = 'SMS'
    
    @extend_schema(
        tags=['Notification System'],
        summary="Create SMS channel",
        description="""
        Create a new SMS notification channel.
        
        Required configuration fields:
        - provider: SMS provider (twilio, nexmo, or aws_sns)
        - api_key: API key for the SMS provider
        
        For Twilio:
        - account_sid: Twilio account SID
        - from_number: Phone number to send from
        
        For Nexmo:
        - api_secret: API secret
        - from_number: Phone number to send from
        
        For AWS SNS:
        - aws_region: AWS region
        - aws_access_key: AWS access key
        - aws_secret_key: AWS secret key
        """,
        request=SMSChannelSerializer,
        responses={201: SMSChannelSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new SMS notification channel.
        """
        return super().create(request, *args, **kwargs) 