from rest_framework import serializers
from mitre.models import AlertMitreMapping, IncidentMitreMapping, ObservableMitreMapping
from .mitre_technique_serializers import MitreTechniqueSerializer


class AlertMitreMappingSerializer(serializers.ModelSerializer):
    """
    Serializer for mappings between Alerts and MITRE ATT&CK Techniques
    """
    technique_detail = MitreTechniqueSerializer(source='technique', read_only=True)
    
    class Meta:
        model = AlertMitreMapping
        fields = ['id', 'alert', 'technique', 'technique_detail', 'confidence', 'auto_detected', 'created_at']
        read_only_fields = ['id', 'created_at']
        
    def validate(self, data):
        """Validate that the mapping doesn't already exist"""
        alert = data.get('alert')
        technique = data.get('technique')
        
        # Check if we're updating an existing record
        instance = getattr(self, 'instance', None)
        if instance:
            # If we're not changing the alert or technique, it's valid
            if instance.alert == alert and instance.technique == technique:
                return data
                
        # Check if a mapping already exists
        if AlertMitreMapping.objects.filter(alert=alert, technique=technique).exists():
            raise serializers.ValidationError(
                "This alert is already mapped to this MITRE technique."
            )
            
        return data


class IncidentMitreMappingSerializer(serializers.ModelSerializer):
    """
    Serializer for mappings between Incidents and MITRE ATT&CK Techniques
    """
    technique_detail = MitreTechniqueSerializer(source='technique', read_only=True)
    
    class Meta:
        model = IncidentMitreMapping
        fields = ['id', 'incident', 'technique', 'technique_detail', 'confidence', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']
        
    def validate(self, data):
        """Validate that the mapping doesn't already exist"""
        incident = data.get('incident')
        technique = data.get('technique')
        
        # Check if we're updating an existing record
        instance = getattr(self, 'instance', None)
        if instance:
            # If we're not changing the incident or technique, it's valid
            if instance.incident == incident and instance.technique == technique:
                return data
                
        # Check if a mapping already exists
        if IncidentMitreMapping.objects.filter(incident=incident, technique=technique).exists():
            raise serializers.ValidationError(
                "This incident is already mapped to this MITRE technique."
            )
            
        return data


class ObservableMitreMappingSerializer(serializers.ModelSerializer):
    """
    Serializer for mappings between Observables and MITRE ATT&CK Techniques
    """
    technique_detail = MitreTechniqueSerializer(source='technique', read_only=True)
    
    class Meta:
        model = ObservableMitreMapping
        fields = ['id', 'observable', 'technique', 'technique_detail', 'confidence', 'auto_detected', 'created_at']
        read_only_fields = ['id', 'created_at']
        
    def validate(self, data):
        """Validate that the mapping doesn't already exist"""
        observable = data.get('observable')
        technique = data.get('technique')
        
        # Check if we're updating an existing record
        instance = getattr(self, 'instance', None)
        if instance:
            # If we're not changing the observable or technique, it's valid
            if instance.observable == observable and instance.technique == technique:
                return data
                
        # Check if a mapping already exists
        if ObservableMitreMapping.objects.filter(observable=observable, technique=technique).exists():
            raise serializers.ValidationError(
                "This observable is already mapped to this MITRE technique."
            )
            
        return data 