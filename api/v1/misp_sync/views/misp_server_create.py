from rest_framework import status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse
from api.core.responses import success_response, created_response, error_response
from api.v1.misp_sync.models import MISPServer
from api.v1.misp_sync.serializers import MISPServerCreateSerializer


class MISPServerCreateMixin:
    """
    Mixin for creating MISP server endpoints.
    """
    
    @extend_schema(
        summary="Create a new MISP server",
        description="Creates a new MISP server configuration for synchronization",
        request=MISPServerCreateSerializer,
        responses={
            201: OpenApiResponse(description="MISP server created successfully"),
            400: OpenApiResponse(description="Invalid request data")
        }
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new MISP server.
        """
        serializer = MISPServerCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            instance = serializer.save()
            return created_response(
                serializer.data,
                message="MISP server created successfully"
            )
        
        return error_response(
            message="Failed to create MISP server",
            errors=serializer.errors
        ) 