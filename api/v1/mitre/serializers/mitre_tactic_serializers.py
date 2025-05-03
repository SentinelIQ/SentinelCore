from rest_framework import serializers
from mitre.models import MitreTactic


class MitreTacticSerializer(serializers.ModelSerializer):
    """
    Serializer for MITRE ATT&CK Tactics with basic fields
    """
    class Meta:
        model = MitreTactic
        fields = ['id', 'external_id', 'name', 'description']
        read_only_fields = ['id', 'external_id', 'name', 'description']


class MitreTacticDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for MITRE ATT&CK Tactics including technique count
    """
    technique_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MitreTactic
        fields = ['id', 'external_id', 'name', 'description', 'technique_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'external_id', 'name', 'description', 'created_at', 'updated_at']
    
    def get_technique_count(self, obj):
        """Get count of techniques associated with this tactic"""
        return obj.techniques.count() 