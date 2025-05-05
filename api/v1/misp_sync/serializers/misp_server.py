from rest_framework import serializers
from api.v1.misp_sync.models import MISPServer
from django.contrib.auth import get_user_model

User = get_user_model()


class UserLightSerializer(serializers.ModelSerializer):
    """
    Lightweight User serializer used in MISP server responses.
    """
    class Meta:
        model = User
        fields = ['id', 'username']


class MISPServerSerializer(serializers.ModelSerializer):
    """
    Base serializer for MISP Server instances.
    """
    created_by = UserLightSerializer(read_only=True)
    
    class Meta:
        model = MISPServer
        fields = [
            'id', 'name', 'url', 'description', 'verify_ssl', 
            'is_active', 'last_sync', 'sync_interval_hours',
            'company', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_sync']


class MISPServerDetailSerializer(MISPServerSerializer):
    """
    Detailed serializer for MISP Server instances with additional information.
    """
    class Meta(MISPServerSerializer.Meta):
        # Additionally add stats or related data if needed
        pass


class MISPServerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating MISP Server instances.
    """
    class Meta:
        model = MISPServer
        fields = [
            'name', 'url', 'api_key', 'description', 'verify_ssl', 
            'is_active', 'sync_interval_hours', 'company'
        ]
    
    def create(self, validated_data):
        """
        Create a MISP server and set the current user as creator.
        """
        # Get user from the request context
        user = self.context['request'].user
        validated_data['created_by'] = user
        
        # If company is not provided, use the user's company
        if 'company' not in validated_data and not user.is_superuser:
            validated_data['company'] = user.company
            
        return super().create(validated_data) 