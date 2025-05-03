from rest_framework import serializers
from alerts.models import Alert
from companies.models import Company
from api.v1.alerts.enums import AlertSeverityEnum, AlertTLPEnum, AlertPAPEnum
from api.core.utils.enum_utils import enum_to_choices


class AlertCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for alert creation with custom validation.
    """
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        required=False
    )
    
    severity = serializers.ChoiceField(
        choices=enum_to_choices(AlertSeverityEnum),
        default=AlertSeverityEnum.MEDIUM.value
    )
    
    tlp = serializers.ChoiceField(
        choices=enum_to_choices(AlertTLPEnum),
        default=AlertTLPEnum.AMBER.value
    )
    
    pap = serializers.ChoiceField(
        choices=enum_to_choices(AlertPAPEnum),
        default=AlertPAPEnum.AMBER.value
    )
    
    class Meta:
        model = Alert
        fields = [
            'title', 'description', 'severity', 'source', 'source_ref',
            'tags', 'tlp', 'pap', 'date', 'company', 'observable_data'
        ]
    
    def create(self, validated_data):
        """
        Automatically assigns user and company when creating an alert.
        """
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        
        # Only override company if the user has one and none was provided
        if request.user.company and 'company' not in validated_data:
            validated_data['company'] = request.user.company
            
        return super().create(validated_data) 