from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from api.core.responses import success_response, error_response
from api.v1.misp_sync.models import MISPServer
from api.v1.misp_sync.serializers import MISPServerDetailSerializer
from pymisp import PyMISP
import logging

logger = logging.getLogger('api')


class MISPServerDetailMixin:
    """
    Mixin for MISP server detail operations.
    """
    
    @extend_schema(
        summary="Retrieve MISP server details",
        description="Get detailed information about a specific MISP server configuration",
        responses={
            200: MISPServerDetailSerializer,
            404: OpenApiResponse(description="MISP server not found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve details of a specific MISP server.
        """
        try:
            instance = self.get_object()
            serializer = MISPServerDetailSerializer(instance)
            return success_response(data=serializer.data)
        except NotFound:
            logger.error(f"MISP server not found with ID: {kwargs.get('pk')}")
            return error_response(
                message="MISP server not found",
                errors={"detail": f"No MISP server found with ID: {kwargs.get('pk')}"},
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Test MISP server connection",
        description="Tests the connection to the MISP server using the configured API key",
        responses={
            200: OpenApiResponse(description="Connection successful"),
            400: OpenApiResponse(description="Connection failed")
        }
    )
    @action(detail=True, methods=['post'])
    def test_connection(self, request, *args, **kwargs):
        """
        Test the connection to a MISP server.
        """
        try:
            instance = self.get_object()
            
            try:
                # Initialize PyMISP to test the connection
                misp = PyMISP(instance.url, instance.api_key, instance.verify_ssl)
                
                # Attempt to get MISP version using the correct API
                # The get_version method doesn't exist in current PyMISP versions
                # Using the request method instead to query the version endpoint
                result = misp.direct_call('servers/getVersion')
                
                # Check if we got a valid response
                if isinstance(result, dict) and 'version' in result:
                    # Connection successful
                    version = result.get('version')
                    logger.info(f"Successfully connected to MISP server {instance.name} (ID: {instance.id}). Version: {version}")
                    
                    return success_response(
                        data={
                            "server_id": instance.id,
                            "status": "connected",
                            "version": version,
                            "url": instance.url
                        },
                        message=f"Successfully connected to MISP server. Version: {version}"
                    )
                else:
                    # Connection succeeded but got unexpected response
                    logger.warning(f"Connected to MISP server {instance.name} (ID: {instance.id}) but got unexpected response: {result}")
                    
                    return success_response(
                        data={
                            "server_id": instance.id,
                            "status": "connected",
                            "response": str(result),
                            "url": instance.url
                        },
                        message="Connected to MISP server but received unexpected response format."
                    )
                    
            except Exception as e:
                # Connection failed
                logger.error(f"Failed to connect to MISP server {instance.name} (ID: {instance.id}): {str(e)}")
                
                return error_response(
                    message="Failed to connect to MISP server",
                    errors={"detail": str(e)}
                )
        except NotFound:
            logger.error(f"MISP server not found with ID: {kwargs.get('pk')}")
            return error_response(
                message="MISP server not found",
                errors={"detail": f"No MISP server found with ID: {kwargs.get('pk')}"},
                status_code=status.HTTP_404_NOT_FOUND
            ) 