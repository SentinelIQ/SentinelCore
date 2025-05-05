from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from ..serializers import (
    CustomTokenObtainPairSerializer, 
    TokenRefreshResponseSerializer,
    EmailPasswordTokenObtainSerializer,
    TokenObtainPairResponseSerializer
)
from api.core.responses import success_response, error_response
import logging

logger = logging.getLogger('api.auth')


@extend_schema(tags=['Authentication & Access Control'])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens with user information.
    Replaces the default SimpleJWT view to include additional data in the response.
    """
    serializer_class = CustomTokenObtainPairSerializer
    entity_type = 'auth'
    
    @extend_schema(
        summary="Obtain JWT token via username",
        description=(
            "Get a JWT token using username and password. The response includes both access "
            "and refresh tokens, along with the user's information including role and company. "
            "Use the access token in the Authorization header like 'Bearer <token>' for "
            "authenticated API requests. If the token expires, use the refresh token endpoint "
            "to get a new token."
        ),
        examples=[
            OpenApiExample(
                name="admin_login",
                summary="Authentication as admin",
                description="Use these credentials for an admin user",
                value={
                    "username": "admin_company",
                    "password": "secure-password-example"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="analyst_login",
                summary="Authentication as analyst",
                description="Use these credentials for an analyst user",
                value={
                    "username": "analyst_user",
                    "password": "secure-password-example"
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="JWT token and user information",
                response=TokenObtainPairResponseSerializer,
                examples=[
                    OpenApiExample(
                        name="success_response",
                        summary="Successful authentication",
                        description="Authentication successful with tokens and user details",
                        value={
                            "status": "success",
                            "message": "Authentication successful",
                            "data": {
                                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "user": {
                                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                    "username": "admin_company",
                                    "email": "admin@company.com",
                                    "role": "admin_company",
                                    "is_superuser": False,
                                    "first_name": "Admin",
                                    "last_name": "User",
                                    "company": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                                    "company_name": "Acme Corporation"
                                }
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        name="invalid_credentials",
                        summary="Authentication failed",
                        description="The provided credentials are invalid",
                        value={
                            "status": "error",
                            "message": "Invalid credentials",
                            "code": "authentication_failed"
                        }
                    )
                ]
            )
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


@extend_schema(tags=['Authentication & Access Control'])
class EmailPasswordTokenObtainView(TokenObtainPairView):
    """
    View for authentication using email and password instead of username and password.
    Returns JWT token with user information.
    """
    serializer_class = EmailPasswordTokenObtainSerializer
    entity_type = 'auth'  # Define entity type for RBAC
    
    @extend_schema(
        summary="Obtain JWT token via email",
        description=(
            "Get a JWT token using email and password instead of username and password. "
            "This endpoint is particularly useful for integration with email-based systems. "
            "The response includes access and refresh tokens along with user details. "
            "For API authentication, include the access token in the Authorization header "
            "as 'Bearer <token>'. Access tokens expire as configured in the JWT settings."
        ),
        examples=[
            OpenApiExample(
                name="email_login",
                summary="Authentication via email",
                description="Use email and password for authentication",
                value={
                    "email": "analyst@company.com",
                    "password": "secure-password-example"
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="JWT token and user information",
                response=TokenObtainPairResponseSerializer,
                examples=[
                    OpenApiExample(
                        name="success_response",
                        summary="Successful authentication",
                        description="Authentication successful with tokens and user details",
                        value={
                            "status": "success",
                            "message": "Authentication successful",
                            "data": {
                                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "user": {
                                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                    "username": "analyst_user",
                                    "email": "analyst@company.com",
                                    "role": "analyst_company",
                                    "is_superuser": False,
                                    "first_name": "Analyst",
                                    "last_name": "User",
                                    "company": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                                    "company_name": "Acme Corporation"
                                }
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        name="invalid_credentials",
                        summary="Authentication failed",
                        description="The provided credentials are invalid",
                        value={
                            "status": "error",
                            "message": "User not found with the provided email.",
                            "code": "authentication_failed"
                        }
                    ),
                    OpenApiExample(
                        name="wrong_password",
                        summary="Incorrect password",
                        description="The provided password is incorrect",
                        value={
                            "status": "error",
                            "message": "Incorrect password.",
                            "code": "authentication_failed"
                        }
                    ),
                    OpenApiExample(
                        name="missing_fields",
                        summary="Missing credentials",
                        description="Email or password is missing",
                        value={
                            "status": "error",
                            "message": "Please provide both email and password.",
                            "code": "authorization"
                        }
                    )
                ]
            )
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


@extend_schema(tags=['Authentication & Access Control'])
class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom view for refreshing JWT tokens with user information.
    """
    serializer_class = TokenRefreshResponseSerializer
    entity_type = 'auth'  # Define entity type for RBAC
    
    @extend_schema(
        summary="Refresh JWT token",
        description=(
            "Refresh an existing JWT token to extend its validity. Use this endpoint when "
            "your access token expires but you still have a valid refresh token. The response "
            "includes a new access token. Refresh tokens have a longer lifetime but are "
            "rotated for security. Include the refresh token in the request body."
        ),
        examples=[
            OpenApiExample(
                name="refresh_token",
                summary="Token refresh request",
                description="Request with refresh token to get a new access token",
                value={
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                },
                request_only=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description="New access token",
                examples=[
                    OpenApiExample(
                        name="success_response",
                        summary="Token refreshed successfully",
                        description="New access token successfully generated",
                        value={
                            "status": "success",
                            "message": "Token successfully refreshed",
                            "data": {
                                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Invalid or expired token",
                examples=[
                    OpenApiExample(
                        name="invalid_token",
                        summary="Invalid refresh token",
                        description="The provided refresh token is invalid or expired",
                        value={
                            "status": "error",
                            "message": "Invalid or expired token",
                            "code": "invalid_token"
                        }
                    )
                ]
            )
        }
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