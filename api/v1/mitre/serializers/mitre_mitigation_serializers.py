from rest_framework import serializers
from mitre.models import MitreMitigation
from .mitre_technique_serializers import MitreTechniqueSerializer


class MitreMitigationSerializer(serializers.ModelSerializer):
    """
    Serializer for MITRE ATT&CK Mitigations with basic fields
    """
    class Meta:
        model = MitreMitigation
        fields = ['id', 'external_id', 'name', 'description']
        read_only_fields = ['id', 'external_id', 'name', 'description']


class MitreMitigationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for MITRE ATT&CK Mitigations including technique count
    """
    technique_count = serializers.SerializerMethodField()
    techniques = MitreTechniqueSerializer(many=True, read_only=True)
    
    class Meta:
        model = MitreMitigation
        fields = ['id', 'external_id', 'name', 'description', 'technique_count', 'techniques', 'created_at', 'updated_at']
        read_only_fields = ['id', 'external_id', 'name', 'description', 'created_at', 'updated_at']
    
    def get_technique_count(self, obj):
        """Get count of techniques associated with this mitigation"""
        return obj.techniques.count() 