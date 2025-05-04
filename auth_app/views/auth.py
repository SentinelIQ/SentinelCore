from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.response import Response
from api.core.responses import success_response, error_response
from drf_spectacular.utils import extend_schema, extend_schema_view
import logging

logger = logging.getLogger(__name__)


@extend_schema(tags=['Authentication & Access Control'])
class LoginView(TokenObtainPairView):
    """
    API endpoint for user login.
    """
    
    @extend_schema(
        description="Login with username and password to get a JWT token pair",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "access": {"type": "string"},
                            "refresh": {"type": "string"}
                        }
                    },
                    "message": {"type": "string", "example": "Login successful"}
                }
            }
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Login with username and password to get a JWT token pair.
        """
        response = super().post(request, *args, **kwargs)
        
        # Return standardized response
        return success_response(
            data=response.data,
            message="Login successful"
        )


@extend_schema(tags=['Authentication & Access Control'])
class RefreshTokenView(TokenRefreshView):
    """
    API endpoint for refreshing JWT tokens.
    """
    
    @extend_schema(
        description="Refresh an access token using a refresh token",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "access": {"type": "string"}
                        }
                    },
                    "message": {"type": "string", "example": "Token refreshed successfully"}
                }
            }
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Refresh an access token using a refresh token.
        """
        response = super().post(request, *args, **kwargs)
        
        # Return standardized response
        return success_response(
            data=response.data,
            message="Token refreshed successfully"
        )


@extend_schema(tags=['Authentication & Access Control'])
class LogoutView(APIView):
    """
    API endpoint for user logout.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Logout by blacklisting the refresh token",
        request={
            "type": "object",
            "properties": {
                "refresh": {"type": "string", "description": "The refresh token to blacklist"}
            },
            "required": ["refresh"]
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "message": {"type": "string", "example": "Logout successful"}
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "error"},
                    "message": {"type": "string", "example": "Token is required"}
                }
            }
        }
    )
    def post(self, request):
        """
        Logout by blacklisting the refresh token.
        """
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return error_response(
                    message="Token is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return success_response(
                message="Logout successful",
                status_code=status.HTTP_200_OK
            )
        except TokenError as e:
            logger.error(f"Error during logout: {str(e)}")
            return error_response(
                message="Invalid token",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error during logout: {str(e)}")
            return error_response(
                message="Error occurred during logout",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 