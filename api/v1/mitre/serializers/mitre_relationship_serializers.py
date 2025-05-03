from rest_framework import serializers
from mitre.models import MitreRelationship


class MitreRelationshipSerializer(serializers.ModelSerializer):
    """
    Serializer for MITRE ATT&CK Relationships
    """
    class Meta:
        model = MitreRelationship
        fields = ['id', 'source_id', 'target_id', 'relationship_type', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'source_id', 'target_id', 'relationship_type', 'description', 'created_at', 'updated_at'] 