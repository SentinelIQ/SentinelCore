from rest_framework import serializers
from incidents.models import Incident
from alerts.models import Alert
from auth_app.models import User
from api.v1.alerts.serializers import AlertSerializer
from api.v1.incidents.enums import IncidentStatusEnum, IncidentSeverityEnum, IncidentTLPEnum, IncidentPAPEnum
from api.v1.alerts.enums import AlertStatusEnum
from api.core.utils.enum_utils import enum_to_choices
from .incident_observable import IncidentObservableSerializer
from .incident_task import IncidentTaskSerializer


class IncidentSerializer(serializers.ModelSerializer):
    """
    Primary serializer for the Incident model.
    """
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tlp_display = serializers.CharField(source='get_tlp_display', read_only=True)
    pap_display = serializers.CharField(source='get_pap_display', read_only=True)
    alert_count = serializers.IntegerField(read_only=True)
    
    severity = serializers.ChoiceField(choices=enum_to_choices(IncidentSeverityEnum))
    status = serializers.ChoiceField(choices=enum_to_choices(IncidentStatusEnum))
    tlp = serializers.ChoiceField(choices=enum_to_choices(IncidentTLPEnum))
    pap = serializers.ChoiceField(choices=enum_to_choices(IncidentPAPEnum))
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'severity', 'severity_display',
            'status', 'status_display', 'company', 'created_by',
            'created_at', 'updated_at', 'alert_count', 'tags', 
            'tlp', 'tlp_display', 'pap', 'pap_display',
            'start_date', 'end_date'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'company', 'alert_count', 'end_date']
    
    def validate(self, data):
        """
        Custom validation for the Incident model.
        """
        # If status is being changed to CLOSED, verify that end_date is set
        if 'status' in data and data['status'] == IncidentStatusEnum.CLOSED.value:
            # If end date is not provided, use current date
            data['end_date'] = data.get('end_date') or serializers.CreateOnlyDefault(serializers.timezone.now())
        
        return data
    
    def create(self, validated_data):
        """
        Automatically assigns user and company when creating an incident.
        """
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['company'] = request.user.company
        return super().create(validated_data)


class IncidentUserLightSerializer(serializers.ModelSerializer):
    """
    Simplified User serializer used in IncidentDetailSerializer.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = fields


class AlertLightSerializer(serializers.ModelSerializer):
    """
    Simplified Alert serializer used in IncidentDetailSerializer.
    """
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'severity', 'severity_display',
            'status', 'status_display', 'created_at', 'date',
            'source', 'source_ref', 'tags', 'tlp', 'pap'
        ]
        read_only_fields = fields


class IncidentDetailSerializer(IncidentSerializer):
    """
    Detailed serializer for Incident, used in detail views.
    """
    created_by = IncidentUserLightSerializer(read_only=True)
    assignee = IncidentUserLightSerializer(read_only=True)
    related_alerts = AlertLightSerializer(many=True, read_only=True)
    incident_observables = IncidentObservableSerializer(many=True, read_only=True)
    tasks = IncidentTaskSerializer(many=True, read_only=True)
    observable_count = serializers.IntegerField(read_only=True)
    task_count = serializers.IntegerField(read_only=True)
    
    class Meta(IncidentSerializer.Meta):
        fields = IncidentSerializer.Meta.fields + [
            'related_alerts', 'assignee', 'incident_observables', 'tasks',
            'timeline', 'observable_count', 'task_count', 'custom_fields',
            'linked_entities', 'sentinelvision_responders'
        ]


class IncidentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for incident creation with custom validation.
    """
    alert_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    
    severity = serializers.ChoiceField(
        choices=enum_to_choices(IncidentSeverityEnum),
        default=IncidentSeverityEnum.MEDIUM.value
    )
    
    status = serializers.ChoiceField(
        choices=enum_to_choices(IncidentStatusEnum),
        default=IncidentStatusEnum.OPEN.value
    )
    
    tlp = serializers.ChoiceField(
        choices=enum_to_choices(IncidentTLPEnum),
        default=IncidentTLPEnum.AMBER.value
    )
    
    pap = serializers.ChoiceField(
        choices=enum_to_choices(IncidentPAPEnum),
        default=IncidentPAPEnum.AMBER.value
    )
    
    class Meta:
        model = Incident
        fields = [
            'title', 'description', 'severity', 'status', 'alert_ids',
            'tags', 'tlp', 'pap', 'start_date'
        ]
    
    def validate_alert_ids(self, value):
        """
        Validates that all alerts exist and belong to the same company.
        """
        if not value:
            return value
        
        request = self.context.get('request')
        company = request.user.company
        
        # Filter alerts by company
        if not request.user.is_superuser:
            alerts = Alert.objects.filter(id__in=value, company=company)
        else:
            alerts = Alert.objects.filter(id__in=value)
        
        # Verify that all IDs were found
        if len(alerts) != len(value):
            raise serializers.ValidationError(
                "One or more alerts don't exist or you don't have permission to access them."
            )
        
        return value
    
    def create(self, validated_data):
        """
        Creates an incident and adds the related alerts.
        """
        alert_ids = validated_data.pop('alert_ids', [])
        request = self.context.get('request')
        
        # Add company and creator user
        validated_data['company'] = request.user.company
        validated_data['created_by'] = request.user
        
        # Create the incident
        incident = Incident.objects.create(**validated_data)
        
        # Add related alerts, if any
        if alert_ids:
            alerts = Alert.objects.filter(id__in=alert_ids)
            incident.related_alerts.set(alerts)
            
            # Update the status of alerts to "escalated"
            alerts.update(status=AlertStatusEnum.ESCALATED.value)
        
        return incident


class IncidentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for incident updates, with limited fields.
    """
    add_alert_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    
    remove_alert_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    
    severity = serializers.ChoiceField(choices=enum_to_choices(IncidentSeverityEnum))
    status = serializers.ChoiceField(choices=enum_to_choices(IncidentStatusEnum))
    tlp = serializers.ChoiceField(choices=enum_to_choices(IncidentTLPEnum))
    pap = serializers.ChoiceField(choices=enum_to_choices(IncidentPAPEnum))
    
    class Meta:
        model = Incident
        fields = [
            'title', 'description', 'severity', 'status', 'add_alert_ids', 
            'remove_alert_ids', 'tags', 'tlp', 'pap', 'start_date', 'end_date'
        ]
        read_only_fields = ['end_date']
    
    def validate(self, data):
        """
        Validates the data for incident updates.
        """
        # If status is changing to CLOSED, set end_date to now if not provided
        if 'status' in data and data['status'] == IncidentStatusEnum.CLOSED.value:
            if not self.instance.end_date and not data.get('end_date'):
                data['end_date'] = serializers.CreateOnlyDefault(serializers.timezone.now())
        return data
    
    def validate_add_alert_ids(self, value):
        """
        Validates the alerts to be added to the incident.
        """
        if not value:
            return value
        
        request = self.context.get('request')
        company = request.user.company
        
        # Filter alerts by company if not superuser
        if not request.user.is_superuser:
            alerts = Alert.objects.filter(id__in=value, company=company)
        else:
            alerts = Alert.objects.filter(id__in=value)
        
        # Verify that all IDs were found
        if len(alerts) != len(value):
            raise serializers.ValidationError(
                "One or more alerts don't exist or you don't have permission to access them."
            )
        
        # Check if any alerts are already linked to this incident
        if self.instance:
            already_linked = self.instance.related_alerts.filter(id__in=value).values_list('id', flat=True)
            if already_linked:
                raise serializers.ValidationError(
                    f"The following alerts are already linked to this incident: {already_linked}"
                )
        
        return value
    
    def update(self, instance, validated_data):
        """
        Updates an incident and manages related alerts.
        """
        add_alert_ids = validated_data.pop('add_alert_ids', [])
        remove_alert_ids = validated_data.pop('remove_alert_ids', [])
        
        # Update the instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Add new alerts
        if add_alert_ids:
            alerts_to_add = Alert.objects.filter(id__in=add_alert_ids)
            for alert in alerts_to_add:
                instance.related_alerts.add(alert)
                alert.status = AlertStatusEnum.ESCALATED.value
                alert.save(update_fields=['status'])
        
        # Remove alerts
        if remove_alert_ids:
            instance.related_alerts.remove(*remove_alert_ids)
        
        return instance 