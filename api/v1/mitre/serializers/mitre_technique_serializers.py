from rest_framework import serializers
from mitre.models import MitreTechnique
from .mitre_tactic_serializers import MitreTacticSerializer


class MitreTechniqueSerializer(serializers.ModelSerializer):
    """
    Serializer for MITRE ATT&CK Techniques with basic fields
    """
    class Meta:
        model = MitreTechnique
        fields = ['id', 'external_id', 'name', 'description', 'platforms', 'is_subtechnique']
        read_only_fields = ['id', 'external_id', 'name', 'description', 'platforms', 'is_subtechnique']


class MitreTechniqueDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for MITRE ATT&CK Techniques with related entities
    """
    tactics = MitreTacticSerializer(many=True, read_only=True)
    parent = serializers.SerializerMethodField()
    subtechniques_count = serializers.SerializerMethodField()
    alert_count = serializers.SerializerMethodField()
    incident_count = serializers.SerializerMethodField()
    observable_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MitreTechnique
        fields = [
            'id', 'external_id', 'name', 'description', 'platforms', 
            'detection', 'is_subtechnique', 'tactics', 'parent',
            'subtechniques_count', 'alert_count', 'incident_count', 
            'observable_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'external_id', 'name', 'description', 'platforms', 
            'detection', 'is_subtechnique', 'created_at', 'updated_at'
        ]
    
    def get_parent(self, obj):
        """Get parent technique if this is a subtechnique"""
        if obj.parent_technique:
            return {
                'id': obj.parent_technique.id,
                'external_id': obj.parent_technique.external_id,
                'name': obj.parent_technique.name
            }
        return None
    
    def get_subtechniques_count(self, obj):
        """Get count of subtechniques if this is a parent technique"""
        return obj.subtechniques.count()
    
    def get_alert_count(self, obj):
        """Get count of alerts mapped to this technique"""
        return obj.alerts.count()
    
    def get_incident_count(self, obj):
        """Get count of incidents mapped to this technique"""
        return obj.incidents.count()
    
    def get_observable_count(self, obj):
        """Get count of observables mapped to this technique"""
        return obj.observables.count() 