from rest_framework import serializers
from api.v1.misp_sync.models import MISPAttribute, MISPEvent
from api.v1.misp_sync.enums import MISPDistributionEnum


class MISPEventLightSerializer(serializers.ModelSerializer):
    """
    Lightweight MISP Event serializer used in MISP attribute responses.
    """
    class Meta:
        model = MISPEvent
        fields = ['id', 'misp_id', 'info', 'company']


class MISPAttributeSerializer(serializers.ModelSerializer):
    """
    Base serializer for MISP Attribute instances.
    """
    event = MISPEventLightSerializer(read_only=True)
    distribution_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MISPAttribute
        fields = [
            'id', 'uuid', 'misp_id', 'misp_uuid', 'type', 'category',
            'value', 'to_ids', 'distribution', 'distribution_display',
            'timestamp', 'comment', 'tags', 'event', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uuid', 'misp_id', 'misp_uuid', 'created_at', 'updated_at',
            'event', 'timestamp'
        ]
    
    def get_distribution_display(self, obj):
        """Get the display name for the distribution level."""
        try:
            return MISPDistributionEnum(obj.distribution).name
        except (ValueError, TypeError):
            return "UNKNOWN"


class MISPAttributeDetailSerializer(MISPAttributeSerializer):
    """
    Detailed serializer for MISP Attribute instances.
    Includes raw data and additional fields.
    """
    class Meta(MISPAttributeSerializer.Meta):
        fields = MISPAttributeSerializer.Meta.fields + ['raw_data'] 