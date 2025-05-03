from rest_framework import serializers
from observables.models import Observable
from api.v1.observables.enums import ObservableTypeEnum, ObservableTLPEnum
from api.core.utils.enum_utils import enum_to_choices


class ObservableCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating observables.
    """
    # Use enum-based choices for fields
    type = serializers.ChoiceField(choices=enum_to_choices(ObservableTypeEnum))
    tlp = serializers.ChoiceField(
        choices=enum_to_choices(ObservableTLPEnum),
        default=ObservableTLPEnum.AMBER.value
    )
    
    class Meta:
        model = Observable
        fields = [
            'type',
            'value',
            'description',
            'tags',
            'tlp',
            'alert',
            'incident',
            'is_ioc',
        ]
        
    def validate_value(self, value):
        """
        Validate observable value format based on type.
        """
        observable_type = self.initial_data.get('type')
        
        # Perform validation based on observable type
        # This is a simplified validation - in a real system you'd have more complex rules
        if observable_type == ObservableTypeEnum.IP.value:
            # Simple IP validation
            import re
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', value):
                raise serializers.ValidationError("Invalid IP address format")
        elif observable_type == ObservableTypeEnum.URL.value:
            # Simple URL validation
            if not value.startswith(('http://', 'https://')):
                raise serializers.ValidationError("URL must start with http:// or https://")
        
        return value
        
    def validate(self, data):
        """
        Ensure company consistency.
        """
        request = self.context.get('request')
        user = request.user
        
        # If alert is provided, ensure company matches user company
        if 'alert' in data and data['alert'].company != user.company:
            raise serializers.ValidationError(
                "Alert must belong to your company"
            )
        
        # If incident is provided, ensure company matches user company
        if 'incident' in data and data['incident'].company != user.company:
            raise serializers.ValidationError(
                "Incident must belong to your company"
            )
        
        return data 