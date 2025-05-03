from rest_framework import serializers
from auth_app.models import User


class UserNestedSerializer(serializers.ModelSerializer):
    """
    Simplified User serializer used in CompanyDetailSerializer.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active']
        read_only_fields = fields 