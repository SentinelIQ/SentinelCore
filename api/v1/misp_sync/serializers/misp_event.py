from rest_framework import serializers
from api.v1.misp_sync.models import MISPEvent, MISPServer
from api.v1.misp_sync.enums import MISPThreatLevelEnum, MISPAnalysisEnum, MISPDistributionEnum
from api.core.utils.enum_utils import enum_to_choices


class MISPServerLightSerializer(serializers.ModelSerializer):
    """
    Lightweight MISP Server serializer used in MISP event responses.
    """
    class Meta:
        model = MISPServer
        fields = ['id', 'name', 'url']


class MISPEventSerializer(serializers.ModelSerializer):
    """
    Base serializer for MISP Event instances.
    """
    misp_server = MISPServerLightSerializer(read_only=True)
    threat_level_display = serializers.SerializerMethodField()
    analysis_display = serializers.SerializerMethodField()
    distribution_display = serializers.SerializerMethodField()
    attribute_count = serializers.IntegerField(read_only=True, source='attributes.count')
    
    class Meta:
        model = MISPEvent
        fields = [
            'id', 'uuid', 'misp_id', 'misp_uuid', 'info', 'date',
            'threat_level_id', 'threat_level_display', 'analysis', 
            'analysis_display', 'distribution', 'distribution_display', 
            'published', 'tags', 'org_name', 'orgc_name', 'timestamp',
            'misp_server', 'company', 'attribute_count', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uuid', 'misp_id', 'misp_uuid', 'created_at', 'updated_at',
            'company', 'misp_server', 'timestamp', 'attribute_count'
        ]
    
    def get_threat_level_display(self, obj):
        """Get the display name for the threat level ID."""
        try:
            return MISPThreatLevelEnum(obj.threat_level_id).name
        except (ValueError, TypeError):
            return "UNKNOWN"
    
    def get_analysis_display(self, obj):
        """Get the display name for the analysis level."""
        try:
            return MISPAnalysisEnum(obj.analysis).name
        except (ValueError, TypeError):
            return "UNKNOWN"
    
    def get_distribution_display(self, obj):
        """Get the display name for the distribution level."""
        try:
            return MISPDistributionEnum(obj.distribution).name
        except (ValueError, TypeError):
            return "UNKNOWN"


class MISPEventDetailSerializer(MISPEventSerializer):
    """
    Detailed serializer for MISP Event instances.
    Includes raw data and additional fields.
    """
    class Meta(MISPEventSerializer.Meta):
        fields = MISPEventSerializer.Meta.fields + ['raw_data'] 