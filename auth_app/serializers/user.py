from rest_framework import serializers
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    company_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'is_active', 'role', 'company', 'company_name']
        read_only_fields = ['id', 'is_active', 'company_name']
    
    def get_company_name(self, obj):
        """Get company name for the user"""
        if obj.company:
            return obj.company.name
        return None


class UserLiteSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for User model with minimal fields.
    Used for references in other serializers.
    """
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'email', 'first_name', 'last_name']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users.
    """
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'role', 'company']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Create a new user with encrypted password"""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating users.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role'] 