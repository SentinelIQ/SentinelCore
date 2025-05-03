from rest_framework import serializers
from observables.models import Observable


class ObservableLightSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for Observable model used in alert context
    """
    class Meta:
        model = Observable
        fields = ['id', 'type', 'value', 'is_ioc', 'tags']
        read_only_fields = fields


class ObservableAddToAlertSerializer(serializers.Serializer):
    """
    Serializer for adding an observable to an alert
    """
    observable = serializers.PrimaryKeyRelatedField(queryset=Observable.objects.all())
    is_ioc = serializers.BooleanField(default=False, help_text="Mark as Indicator of Compromise")
    description = serializers.CharField(required=False, allow_blank=True, help_text="Optional description")
    
    def validate_observable(self, value):
        """
        Ensure the observable belongs to the same company as the alert
        """
        alert = self.context.get('alert')
        if alert and alert.company != value.company:
            raise serializers.ValidationError(
                "Observable must belong to the same company as the alert."
            )
        return value 