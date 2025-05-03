from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, viewsets, serializers
from django.db import connection
from django.conf import settings
from api.core.throttling import PublicEndpointRateThrottle, StandardUserRateThrottle
from api.core.responses import success_response, error_response
from .permissions import CommonPermission
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer, OpenApiExample
import datetime
import logging
import platform

logger = logging.getLogger('api.common')


# Define serializers for clear OpenAPI documentation
class HealthCheckResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    timestamp = serializers.CharField()
    environment = serializers.CharField()
    api_version = serializers.CharField()
    python_version = serializers.CharField()
    checks = serializers.DictField(child=serializers.CharField())


class CompanyInfoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()


class UserPermissionsSerializer(serializers.Serializer):
    is_superuser = serializers.BooleanField()
    is_admin_company = serializers.BooleanField()
    is_analyst_company = serializers.BooleanField()
    is_read_only = serializers.BooleanField()


class UserInfoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()
    last_login = serializers.DateTimeField(allow_null=True)
    date_joined = serializers.DateTimeField()


class WhoAmIResponseSerializer(serializers.Serializer):
    user = UserInfoSerializer()
    company = CompanyInfoSerializer(allow_null=True)
    permissions = UserPermissionsSerializer()


@extend_schema(
    tags=['Common'],
    summary="Health check endpoint",
    description="Returns a 200 OK if the API is up and running",
    responses={
        200: OpenApiResponse(
            description="API is healthy",
            examples=[
                OpenApiExample(
                    name="Healthy Response",
                    value={"status": "healthy"}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint. Returns 200 OK if the API is up and running.
    """
    return Response({"status": "healthy"}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Common'],
    summary="Current user information",
    description="Returns information about the currently authenticated user",
    responses={
        200: OpenApiResponse(
            description="Successfully retrieved user information"
        ),
        401: OpenApiResponse(
            description="User is not authenticated"
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whoami(request):
    """
    Returns information about the currently authenticated user.
    """
    user = request.user
    data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'company': user.company.id if user.company else None,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
        }
    }
    return success_response(data)


@extend_schema(tags=['Common'])
class CommonViewSet(viewsets.GenericViewSet):
    """
    Common API endpoints for system-wide functionality.
    """
    permission_classes = [CommonPermission]
    entity_type = 'common'
    
    @extend_schema(
        summary="Health check",
        description="Check the health of the API and its dependencies",
        responses={
            200: HealthCheckResponseSerializer,
            503: HealthCheckResponseSerializer
        }
    )
    def health_check(self, request):
        """
        Check the health of the API and its dependencies.
        
        This endpoint is public and returns information about:
        - Database status
        - Runtime environment
        - Version information
        """
        # Check database connection
        db_ok = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_ok = cursor.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
        
        # Build response
        health_data = {
            'status': 'healthy' if db_ok else 'unhealthy',
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'environment': settings.ENVIRONMENT if hasattr(settings, 'ENVIRONMENT') else 'development',
            'api_version': 'v1',
            'python_version': platform.python_version(),
            'checks': {
                'database': 'connected' if db_ok else 'disconnected',
            }
        }
        
        response_status = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        
        # Use direct Response to maintain the health_data structure for backward compatibility
        return Response(health_data, status=response_status)
    
    @extend_schema(
        summary="User information",
        description="Get information about the currently authenticated user",
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='StandardizedWhoAmIResponse',
                    fields={
                        'status': serializers.CharField(),
                        'message': serializers.CharField(),
                        'data': WhoAmIResponseSerializer()
                    }
                )
            )
        }
    )
    def whoami(self, request):
        """
        Return information about the authenticated user.
        
        This endpoint requires authentication and returns:
        - User information
        - Permissions
        - Company information (if applicable)
        """
        user = request.user
        
        # Prepare company information if it exists
        company_info = None
        if hasattr(user, 'company') and user.company:
            company_info = {
                'id': user.company.id,
                'name': user.company.name,
                'created_at': user.company.created_at,
            }
        
        # Build response with standard format
        user_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'last_login': user.last_login,
                'date_joined': user.date_joined,
            },
            'company': company_info,
            'permissions': {
                'is_superuser': user.is_superuser,
                'is_admin_company': hasattr(user, 'is_admin_company') and user.is_admin_company,
                'is_analyst_company': hasattr(user, 'is_analyst_company') and user.is_analyst_company,
                'is_read_only': hasattr(user, 'is_read_only') and user.is_read_only,
            }
        }
        
        return success_response(
            data=user_data,
            message="User information retrieved successfully"
        ) 