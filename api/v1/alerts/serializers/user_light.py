from rest_framework import serializers
from auth_app.models import User


class UserLightSerializer(serializers.ModelSerializer):
    """
    Simplified User serializer used in AlertDetailSerializer.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = fields 