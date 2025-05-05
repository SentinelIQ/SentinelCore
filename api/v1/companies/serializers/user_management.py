from rest_framework import serializers


class DeactivateUsersSerializer(serializers.Serializer):
    """
    Serializer for deactivating multiple users in a company.
    """
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of user IDs to deactivate"
    ) 