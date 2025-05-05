from rest_framework import serializers


class NotificationTestSerializer(serializers.Serializer):
    """
    Serializer for notification channel testing.
    """
    channel_id = serializers.IntegerField(
        required=True,
        help_text="ID of the notification channel to test"
    )
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        default="This is a test notification from SentinelIQ.",
        help_text="Custom test message (optional)"
    ) 