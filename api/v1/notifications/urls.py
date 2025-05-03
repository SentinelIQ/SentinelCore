from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.views import (
    NotificationViewSet, 
    NotificationChannelViewSet,
    UserNotificationPreferenceViewSet,
    NotificationRuleViewSet,
    NotificationTestView,
    # Views específicas para cada tipo de canal
    EmailChannelCreateView,
    SlackChannelCreateView,
    MattermostChannelCreateView,
    WebhookChannelCreateView,
    SMSChannelCreateView
)

# Create a router for API endpoints
router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'channels', NotificationChannelViewSet, basename='notification-channel')
router.register(r'rules', NotificationRuleViewSet, basename='notification-rule')

# Notification API URL patterns with kebab-case
urlpatterns = [
    # Notification endpoints
    path('', include(router.urls)),
    
    # User notification preferences endpoints - support both integer and UUID IDs
    path('preferences/<int:user_id>/', 
         UserNotificationPreferenceViewSet.as_view({'get': 'retrieve', 'patch': 'update'}), 
         name='user-notification-preferences'),
         
    # Test notification endpoint
    path('test/', NotificationTestView.as_view(), name='notification-test'),
    
    # Channel-specific creation endpoints
    path('channels/email/', EmailChannelCreateView.as_view(), name='email-channel-create'),
    path('channels/slack/', SlackChannelCreateView.as_view(), name='slack-channel-create'),
    path('channels/mattermost/', MattermostChannelCreateView.as_view(), name='mattermost-channel-create'),
    path('channels/webhook/', WebhookChannelCreateView.as_view(), name='webhook-channel-create'),
    path('channels/sms/', SMSChannelCreateView.as_view(), name='sms-channel-create'),
] 