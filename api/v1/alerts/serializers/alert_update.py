from rest_framework import serializers
from alerts.models import Alert
from api.v1.alerts.enums import AlertStatusEnum, AlertSeverityEnum, AlertTLPEnum, AlertPAPEnum
from api.core.utils.enum_utils import enum_to_choices


class AlertUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for alert updates, with limited fields.
    """
    severity = serializers.ChoiceField(
        choices=enum_to_choices(AlertSeverityEnum)
    )
    
    status = serializers.ChoiceField(
        choices=enum_to_choices(AlertStatusEnum)
    )
    
    tlp = serializers.ChoiceField(
        choices=enum_to_choices(AlertTLPEnum)
    )
    
    pap = serializers.ChoiceField(
        choices=enum_to_choices(AlertPAPEnum)
    )
    
    class Meta:
        model = Alert
        fields = [
            'title', 'description', 'severity', 'status', 'source_ref',
            'tags', 'tlp', 'pap'
        ]
    
    def validate_status(self, value):
        """
        Validation to prevent manual change to 'escalated' status.
        """
        if self.instance.status == AlertStatusEnum.ESCALATED.value and value != AlertStatusEnum.ESCALATED.value:
            raise serializers.ValidationError(
                "Cannot change the status of an alert that has already been escalated."
            )
        
        if value == AlertStatusEnum.ESCALATED.value:
            raise serializers.ValidationError(
                "To escalate an alert, use the specific escalation endpoint."
            )
        
        return value 