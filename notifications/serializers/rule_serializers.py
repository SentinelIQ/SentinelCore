from rest_framework import serializers
from django.contrib.auth import get_user_model

from notifications.models import NotificationRule, NotificationChannel
from companies.serializers import CompanySerializer
from .channel_serializers import NotificationChannelSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Simple serializer for User model.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class NotificationRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationRule model.
    """
    channels_data = NotificationChannelSerializer(source='channels', many=True, read_only=True)
    company_data = CompanySerializer(source='company', read_only=True)
    created_by_data = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = NotificationRule
        fields = [
            'id', 'name', 'description', 'event_type', 'is_active',
            'conditions', 'message_template', 'custom_event_id',
            'channels', 'channels_data', 'company', 'company_data',
            'created_by', 'created_by_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate rule configuration.
        """
        # Check that the event type is valid
        event_type = data.get('event_type')
        if event_type == 'custom' and not data.get('custom_event_id'):
            raise serializers.ValidationError(
                {"custom_event_id": "Custom event ID is required when event type is 'custom'"}
            )
            
        # Validate message template
        message_template = data.get('message_template')
        if message_template and len(message_template) < 10:
            raise serializers.ValidationError(
                {"message_template": "Message template must be at least a few sentences long"}
            )
            
        return data
    
    def validate_channels(self, channels):
        """
        Validate that channels exist and are enabled.
        """
        if not channels:
            raise serializers.ValidationError("At least one notification channel must be selected")
            
        for channel in channels:
            if not channel.is_enabled:
                raise serializers.ValidationError(
                    f"Channel '{channel.name}' is disabled and cannot be used in rules"
                )
        
        return channels 