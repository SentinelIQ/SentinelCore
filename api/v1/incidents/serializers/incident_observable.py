from rest_framework import serializers
from incidents.models import IncidentObservable
from observables.models import Observable


class ObservableLightSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for Observable model used in incident context
    """
    class Meta:
        model = Observable
        fields = ['id', 'type', 'value', 'is_ioc', 'tags']
        read_only_fields = fields


class IncidentObservableSerializer(serializers.ModelSerializer):
    """
    Serializer for the IncidentObservable through model
    """
    observable = ObservableLightSerializer(read_only=True)
    
    class Meta:
        model = IncidentObservable
        fields = ['id', 'observable', 'is_ioc', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class IncidentObservableCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating IncidentObservable relationships
    """
    class Meta:
        model = IncidentObservable
        fields = ['observable', 'is_ioc', 'description']
        
    def validate_observable(self, value):
        """
        Ensure the observable belongs to the same company as the incident
        """
        incident = self.context.get('incident')
        if incident and incident.company != value.company:
            raise serializers.ValidationError(
                "Observable must belong to the same company as the incident."
            )
        return value 