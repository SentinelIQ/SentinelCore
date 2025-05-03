from rest_framework import serializers
from notifications.models import Notification, NotificationDeliveryStatus
from auth_app.serializers import UserLiteSerializer
from companies.models import Company

class NotificationDeliveryStatusSerializer(serializers.ModelSerializer):
    """Serializer for notification delivery statuses"""
    
    class Meta:
        model = NotificationDeliveryStatus
        fields = [
            'id', 'status', 'channel', 'sent_at', 
            'delivered_at', 'read_at', 'error_message'
        ]
        read_only_fields = ['id', 'sent_at', 'delivered_at', 'read_at']

class NotificationLiteSerializer(serializers.ModelSerializer):
    """Lite serializer for notifications, used in listings and references"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'category', 'priority', 
            'created_at', 'is_company_wide'
        ]
        read_only_fields = ['id', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    """Full serializer for notifications with nested recipient data"""
    recipients = UserLiteSerializer(many=True, read_only=True)
    delivery_statuses = NotificationDeliveryStatusSerializer(
        many=True, read_only=True, source='delivery_statuses.all'
    )
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'category', 'priority',
            'related_object_type', 'related_object_id',
            'created_at', 'updated_at', 'company', 'recipients',
            'is_company_wide', 'delivery_statuses'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new notifications"""
    recipient_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        required=True  # Make company field required
    )
    
    class Meta:
        model = Notification
        fields = [
            'title', 'message', 'category', 'priority',
            'related_object_type', 'related_object_id',
            'company', 'recipient_ids', 'is_company_wide'
        ]
    
    def validate(self, data):
        """Validate that either recipient_ids or is_company_wide is provided"""
        recipient_ids = data.get('recipient_ids', [])
        is_company_wide = data.get('is_company_wide', False)
        
        if not recipient_ids and not is_company_wide:
            raise serializers.ValidationError(
                "Either recipient_ids or is_company_wide must be provided"
            )
        
        # Ensure company is set
        if 'company' not in data or not data['company']:
            raise serializers.ValidationError("Company is required")
            
        return data
    
    def create(self, validated_data):
        """Create notification and add recipients"""
        recipient_ids = validated_data.pop('recipient_ids', [])
        notification = super().create(validated_data)
        
        if recipient_ids:
            notification.recipients.set(recipient_ids)
            
        return notification 