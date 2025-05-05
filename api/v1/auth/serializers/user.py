from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from companies.models import Company
from api.v1.auth.enums import UserRoleEnum
from api.core.utils.enum_utils import enum_to_choices
from .company_nested import CompanyNestedSerializer
from drf_spectacular.utils import extend_schema_serializer

User = get_user_model()

@extend_schema_serializer(component_name="APIUserSerializer")
class UserSerializer(serializers.ModelSerializer):
    """
    Complete serializer for the User model.
    """
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=False)
    company = CompanyNestedSerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        source='company',
        queryset=Company.objects.all(),
        required=False,
        write_only=True
    )
    
    role = serializers.ChoiceField(
        choices=enum_to_choices(UserRoleEnum),
        default=UserRoleEnum.ANALYST_COMPANY.value
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'role', 'company', 'company_id',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def validate(self, attrs):
        # Validate password and password_confirm
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })
        
        # If updating (not creating user), password is not required
        if self.instance is None and not password:
            raise serializers.ValidationError({
                "password": "Password is required when creating a user."
            })
        
        # Remove password_confirm from attrs
        if 'password_confirm' in attrs:
            attrs.pop('password_confirm')
            
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance 