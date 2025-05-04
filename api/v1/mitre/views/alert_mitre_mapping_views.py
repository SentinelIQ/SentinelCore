from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from mitre.models import AlertMitreMapping
from api.v1.mitre.serializers import AlertMitreMappingSerializer
from api.core.rbac import HasEntityPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response, error_response
from api.core.viewsets import StandardViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    list=extend_schema(
        summary="List Alert-MITRE Mappings",
        description="Returns a list of mappings between alerts and MITRE ATT&CK techniques.",
        tags=["MITRE Framework"]
    ),
    retrieve=extend_schema(
        summary="Retrieve Alert-MITRE Mapping",
        description="Returns details of a specific mapping between an alert and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    create=extend_schema(
        summary="Create Alert-MITRE Mapping",
        description="Maps an alert to a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    update=extend_schema(
        summary="Update Alert-MITRE Mapping",
        description="Updates an existing mapping between an alert and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    partial_update=extend_schema(
        summary="Partially Update Alert-MITRE Mapping",
        description="Partially updates an existing mapping between an alert and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    destroy=extend_schema(
        summary="Delete Alert-MITRE Mapping",
        description="Removes a mapping between an alert and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    bulk_delete=extend_schema(
        summary="Bulk Delete Alert-MITRE Mappings",
        description="Removes all mappings for a specific alert.",
        tags=["MITRE Framework"]
    )
)
class AlertMitreMappingView(StandardViewSet):
    """
    API endpoint for managing mappings between Alerts and MITRE ATT&CK Techniques.
    
    This endpoint allows users to map alerts to MITRE ATT&CK techniques, either
    manually or through automatic detection. These mappings help in understanding
    the tactics and techniques used in security alerts.
    """
    queryset = AlertMitreMapping.objects.all()
    serializer_class = AlertMitreMappingSerializer
    permission_classes = [HasEntityPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['alert', 'technique', 'auto_detected', 'confidence']
    search_fields = ['alert__title', 'technique__name', 'technique__external_id']
    ordering_fields = ['created_at', 'confidence']
    ordering = ['-created_at']
    entity_type = 'alertmitremapping'
    
    # Success messages for standardized responses
    success_message_create = "Alert-MITRE mapping created successfully"
    success_message_update = "Alert-MITRE mapping updated successfully"
    success_message_delete = "Alert-MITRE mapping deleted successfully"
    
    def get_queryset(self):
        """
        Filter mappings by tenant isolation
        """
        queryset = super().get_queryset()
        
        # Apply tenant isolation - only show mappings for alerts in the user's company
        if not self.request.user.is_superuser:
            return queryset.filter(alert__company=self.request.user.company)
            
        return queryset
    
    def perform_create(self, serializer):
        """
        Save mapping with metadata
        """
        serializer.save()
    
    @extend_schema(
        summary="Bulk delete mappings",
        description="Delete all MITRE mappings for a specific alert",
        parameters=[
            {
                "name": "alert_id",
                "in": "query",
                "required": True,
                "schema": {"type": "string", "format": "uuid"}
            }
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "deleted_count": {"type": "integer"}
                        }
                    }
                }
            },
            400: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}
        },
        tags=["MITRE Framework"]
    )
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """
        Delete multiple mappings in a single request
        """
        alert_id = request.query_params.get('alert_id')
        if not alert_id:
            return error_response("Alert ID is required", status_code=status.HTTP_400_BAD_REQUEST)
            
        # Apply tenant isolation
        if not request.user.is_superuser:
            mappings = self.queryset.filter(
                alert_id=alert_id, 
                alert__company=request.user.company
            )
        else:
            mappings = self.queryset.filter(alert_id=alert_id)
        
        count = mappings.count()
        mappings.delete()
        
        return success_response(
            data={'deleted_count': count},
            message=f"Successfully deleted {count} mappings"
        ) 