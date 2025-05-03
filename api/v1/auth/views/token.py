from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from ..serializers import (
    CustomTokenObtainPairSerializer, 
    TokenRefreshResponseSerializer,
    EmailPasswordTokenObtainSerializer
)
from api.core.responses import success_response, error_response
import logging

logger = logging.getLogger('api.auth')


@extend_schema(tags=['Authentication'])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens with user information.
    Replaces the default SimpleJWT view to include additional data in the response.
    """
    serializer_class = CustomTokenObtainPairSerializer
    entity_type = 'auth'  # Define entity type for RBAC
    
    @extend_schema(
        summary="Obtain JWT token",
        description="Get a JWT token using username and password",
        examples=[
            OpenApiExample(
                name="Admin Sentinel",
                summary="Authentication as super admin",
                description="Use these credentials for the adminsentinel user",
                value={
                    "username": "adminsentinel",
                    "password": "change-me-in-production"
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(description="JWT token and user information"),
            401: OpenApiResponse(description="Invalid credentials")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            logger.warning(f"Token error: {str(e)}")
            raise InvalidToken(e.args[0])
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return error_response(
                message="Invalid credentials",
                code="authentication_failed",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Format the response according to API standard
        return success_response(
            data=serializer.validated_data,
            message="Authentication successful",
            code=status.HTTP_200_OK
        )


@extend_schema(tags=['Authentication'])
class EmailPasswordTokenObtainView(TokenObtainPairView):
    """
    View for authentication using email and password instead of username and password.
    Returns JWT token with user information.
    """
    serializer_class = EmailPasswordTokenObtainSerializer
    entity_type = 'auth'  # Define entity type for RBAC
    
    @extend_schema(
        summary="Obtain token via email",
        description="Get a JWT token using email and password instead of username and password",
        examples=[
            OpenApiExample(
                name="Admin Sentinel",
                summary="Authentication as super admin",
                description="Use these credentials for the adminsentinel user",
                value={
                    "email": "admin@sentineliq.com",
                    "password": "change-me-in-production"
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(description="JWT token and user information"),
            401: OpenApiResponse(description="Invalid credentials")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            logger.warning(f"Token error: {str(e)}")
            raise InvalidToken(e.args[0])
        except Exception as e:
            logger.error(f"Authentication error via email: {str(e)}")
            return error_response(
                message=str(e),
                code="authentication_failed",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Format the response according to API standard
        return success_response(
            data=serializer.validated_data,
            message="Authentication successful",
            code=status.HTTP_200_OK
        )


@extend_schema(tags=['Authentication'])
class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom view for refreshing JWT tokens with user information.
    """
    serializer_class = TokenRefreshResponseSerializer
    entity_type = 'auth'  # Define entity type for RBAC
    
    @extend_schema(
        summary="Refresh JWT token",
        description="Refresh an existing JWT token to extend its validity"
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            logger.warning(f"Token refresh error: {str(e)}")
            return error_response(
                message="Invalid or expired token",
                code="invalid_token",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Format the response according to API standard
        return success_response(
            data=serializer.validated_data,
            message="Token successfully refreshed",
            code=status.HTTP_200_OK
        ) 