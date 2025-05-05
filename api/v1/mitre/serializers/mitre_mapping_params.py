from rest_framework import serializers


class AlertMitreMappingQuerySerializer(serializers.Serializer):
    """
    Serializer for alert MITRE mapping query parameters.
    """
    alert_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the alert to retrieve mappings for"
    )


class IncidentMitreMappingQuerySerializer(serializers.Serializer):
    """
    Serializer for incident MITRE mapping query parameters.
    """
    incident_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the incident to retrieve mappings for"
    )


class ObservableMitreMappingQuerySerializer(serializers.Serializer):
    """
    Serializer for observable MITRE mapping query parameters.
    """
    observable_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the observable to retrieve mappings for"
    ) 