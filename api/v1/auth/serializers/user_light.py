from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserLightSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing users.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = fields 