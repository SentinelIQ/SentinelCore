from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class TokenObtainPairResponseSerializer(serializers.Serializer):
    """
    Serializer for token obtain pair response schema documentation.
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.JSONField()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that returns user data along with tokens.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        
        # Add user information to the response
        data.update({
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_superuser': user.is_superuser,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company': str(user.company.id) if user.company else None,
                'company_name': user.company.name if user.company else None
            }
        })
        
        return data


class EmailPasswordTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Serializer to obtain JWT token using email and password instead of username/password.
    """
    username_field = User.EMAIL_FIELD
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.EmailField()
        self.fields['password'] = serializers.CharField(
            style={'input_type': 'password'},
            trim_whitespace=False
        )
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        token['email'] = user.email
        return token
    
    def validate(self, attrs):
        email = attrs.get(self.username_field)
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError(
                _('Please provide both email and password.'),
                code='authorization'
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _('User not found with the provided email.'),
                code='authorization'
            )
        
        # Verify credentials
        self.user = authenticate(
            request=self.context.get('request'),
            username=user.username,  # authenticate needs username, not email
            password=password
        )
        
        if not self.user:
            raise serializers.ValidationError(
                _('Incorrect password.'),
                code='authorization'
            )
        
        if self.user is None or not self.user.is_active:
            raise serializers.ValidationError(
                _('Account disabled or invalid credentials.'),
                code='authorization'
            )
        
        refresh = self.get_token(self.user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        # Add user information to the response
        data.update({
            'user': {
                'id': str(self.user.id),
                'username': self.user.username,
                'email': self.user.email,
                'role': self.user.role,
                'is_superuser': self.user.is_superuser,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'company': str(self.user.company.id) if self.user.company else None,
                'company_name': self.user.company.name if self.user.company else None
            }
        })
        
        return data


class TokenRefreshResponseSerializer(TokenRefreshSerializer):
    """
    Serializer for token refresh that also returns user data.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Decode the token to get the user ID
        refresh = RefreshToken(attrs['refresh'])
        user_id = refresh[api_settings.USER_ID_CLAIM]
        
        try:
            user = User.objects.get(id=user_id)
            # Add user information
            data.update({
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_superuser': user.is_superuser,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'company': str(user.company.id) if user.company else None,
                    'company_name': user.company.name if user.company else None
                }
            })
        except User.DoesNotExist:
            pass
        
        return data 