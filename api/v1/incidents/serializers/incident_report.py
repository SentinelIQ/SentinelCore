from rest_framework import serializers


class IncidentReportFormatSerializer(serializers.Serializer):
    """
    Serializer for requesting an incident report in a specific format
    """
    format = serializers.ChoiceField(
        choices=['pdf', 'markdown', 'html'],
        default='pdf',
        help_text="Format of the report to generate"
    )
    include_timeline = serializers.BooleanField(
        default=True,
        help_text="Whether to include the timeline in the report"
    )
    include_observables = serializers.BooleanField(
        default=True,
        help_text="Whether to include observables in the report"
    )
    include_tasks = serializers.BooleanField(
        default=True,
        help_text="Whether to include tasks in the report"
    )
    include_alerts = serializers.BooleanField(
        default=True,
        help_text="Whether to include related alerts in the report"
    )


class IncidentReportSerializer(serializers.Serializer):
    """
    Serializer for incident reports
    """
    incident_id = serializers.UUIDField(read_only=True)
    report_id = serializers.UUIDField(read_only=True)
    format = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    download_url = serializers.URLField(read_only=True)
    status = serializers.CharField(read_only=True)
    size_bytes = serializers.IntegerField(read_only=True, required=False) 