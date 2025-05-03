from .alert_base import AlertSerializer
from .user_light import UserLightSerializer
from .observable_light import ObservableLightSerializer


class AlertDetailSerializer(AlertSerializer):
    """
    Detailed serializer for Alert, used in detail views.
    """
    created_by = UserLightSerializer(read_only=True)
    observables = ObservableLightSerializer(many=True, read_only=True)
    
    class Meta(AlertSerializer.Meta):
        fields = AlertSerializer.Meta.fields + ['incidents', 'observables', 'observable_data', 'external_source', 'raw_payload']
        read_only_fields = AlertSerializer.Meta.read_only_fields + ['incidents', 'observables'] 