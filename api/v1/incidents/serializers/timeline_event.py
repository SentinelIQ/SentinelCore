from rest_framework import serializers
from incidents.models import TimelineEvent


class TimelineEventSerializer(serializers.ModelSerializer):
    """
    Serializer for the TimelineEvent model.
    """
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TimelineEvent
        fields = ['id', 'incident', 'type', 'title', 'message', 'metadata',
                 'user', 'user_name', 'timestamp', 'created_at']
        read_only_fields = ['id', 'created_at', 'user_name']
    
    def get_user_name(self, obj):
        """
        Returns the user's display name.
        """
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.username
        return "System" 