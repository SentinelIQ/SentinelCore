from rest_framework import serializers
from notifications.models import UserNotificationPreference

class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences"""
    
    class Meta:
        model = UserNotificationPreference
        fields = [
            'id', 'user',
            # Email preferences
            'email_alerts', 'email_incidents', 'email_tasks', 'email_reports',
            # In-app preferences
            'in_app_alerts', 'in_app_incidents', 'in_app_tasks', 'in_app_reports',
            # Slack preferences
            'slack_alerts', 'slack_incidents', 'slack_tasks', 'slack_critical_only',
            # SMS preferences
            'sms_critical_only',
            # Digest preferences
            'daily_digest', 'weekly_digest',
            # Metadata
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at'] 