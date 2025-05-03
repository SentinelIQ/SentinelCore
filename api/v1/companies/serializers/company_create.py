from rest_framework import serializers
from companies.models import Company
from auth_app.models import User
from django.db import transaction


class CompanyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for company creation with admin user binding.
    
    Requires creating an admin user (admin_company) for each company.
    Only the superuser can perform this operation.
    """
    # Company fields
    name = serializers.CharField(max_length=255)
    
    # Admin user nested fields - required for API but not stored in Company model
    admin_user = serializers.DictField(write_only=True, required=True)
    
    class Meta:
        model = Company
        fields = ['name', 'admin_user']
    
    def validate(self, data):
        """
        Validate the entire data payload to ensure admin_user is present.
        """
        if 'admin_user' not in data:
            raise serializers.ValidationError({
                "admin_user": "A company administrator is required when creating a new company."
            })
        return data
    
    def validate_admin_user(self, value):
        """
        Validates the admin_user data ensuring all required fields are present
        and the data is valid.
        """
        if not value:
            raise serializers.ValidationError("Company administrator data is required.")
            
        required_fields = ['email', 'password']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"The '{field}' field is required for the company administrator.")
                
        # Validate email uniqueness
        email = value.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already in use.")
            
        # Username is optional - if not provided, use email as username
        username = value.get('username', email)
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("This username is already in use.")
            
        # Make sure role is admin_company
        if 'role' in value and value['role'] != User.Role.ADMIN_COMPANY:
            raise serializers.ValidationError("The company administrator must have the 'admin_company' role.")
            
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Creates the company and binds an admin_company user to it.
        """
        # Extract admin user data
        admin_data = validated_data.pop('admin_user')
        
        # Extract user fields
        email = admin_data.get('email')
        password = admin_data.get('password')
        username = admin_data.get('username', email)  # Default to email if username not provided
        first_name = admin_data.get('first_name', '')
        last_name = admin_data.get('last_name', '')
        
        # Create the company
        company = Company.objects.create(**validated_data)
        
        # Create the admin user
        admin_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.ADMIN_COMPANY,
            company=company
        )
        
        return company 