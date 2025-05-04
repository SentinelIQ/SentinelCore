"""
Notification Views

This module provides API endpoints for managing notifications 
and delivery channels in the SentinelIQ platform.

Notifications represent system messages sent to users through
various channels such as email, Slack, webhooks, and in-app
notifications. This system supports delivery tracking,
user preferences, and message templating.
"""

from api.core.viewsets import StandardViewSet
from drf_spectacular.utils import extend_schema

from .notification_list import NotificationListView
from .notification_detail import NotificationDetailView
from .notification_create import NotificationCreateView
from .notification_mark_read import NotificationMarkReadView
from .notification_test import NotificationTestView

from .channel_list import NotificationChannelListView
from .channel_detail import NotificationChannelDetailView
from .channel_create import NotificationChannelCreateView
from .channel_specific import (
    EmailChannelCreateView,
    SlackChannelCreateView,
    MattermostChannelCreateView,
    WebhookChannelCreateView,
    SMSChannelCreateView
)

from .preference_detail import UserNotificationPreferenceDetailView
from .preference_update import UserNotificationPreferenceUpdateView

from .rule_list import NotificationRuleListView
from .rule_detail import NotificationRuleDetailView
from .rule_create import NotificationRuleCreateView

# View Mixins for Notifications
@extend_schema(tags=['Notification System'])
class NotificationViewSet(
    NotificationListView,
    NotificationDetailView,
    NotificationCreateView,
    NotificationMarkReadView,
    StandardViewSet
):
    """
    ViewSet for managing notifications including
    listing, retrieving, creating, and marking as read.
    """
    entity_type = 'notification'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Notification created successfully"
    success_message_update = "Notification updated successfully"
    success_message_delete = "Notification deleted successfully"

# View Mixins for Notification Channels
@extend_schema(tags=['Notification System'])
class NotificationChannelViewSet(
    NotificationChannelListView,
    NotificationChannelDetailView,
    NotificationChannelCreateView,
    StandardViewSet
):
    """
    ViewSet for managing notification channels including
    listing, retrieving, and creating channels.
    """
    entity_type = 'notification_channel'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Notification channel created successfully"
    success_message_update = "Notification channel updated successfully"
    success_message_delete = "Notification channel deleted successfully"

# View Mixins for User Notification Preferences
@extend_schema(tags=['Notification System'])
class UserNotificationPreferenceViewSet(
    UserNotificationPreferenceDetailView,
    UserNotificationPreferenceUpdateView,
    StandardViewSet
):
    """
    ViewSet for managing user notification preferences including
    retrieving and updating preferences.
    """
    entity_type = 'notification_preference'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Notification preferences created successfully"
    success_message_update = "Notification preferences updated successfully"
    success_message_delete = "Notification preferences deleted successfully"

# View Mixins for Notification Rules
@extend_schema(tags=['Notification System'])
class NotificationRuleViewSet(
    NotificationRuleListView,
    NotificationRuleDetailView,
    NotificationRuleCreateView,
    StandardViewSet
):
    """
    ViewSet for managing notification rules including
    listing, retrieving, creating, updating, and deleting rules.
    """
    entity_type = 'notification_rule'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Notification rule created successfully"
    success_message_update = "Notification rule updated successfully"
    success_message_delete = "Notification rule deleted successfully" 