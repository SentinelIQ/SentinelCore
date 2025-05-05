from rest_framework import filters, status
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from mitre.models import ObservableMitreMapping
from api.v1.mitre.serializers import ObservableMitreMappingSerializer
from api.v1.mitre.serializers.mitre_mapping_params import ObservableMitreMappingQuerySerializer
from api.core.rbac import HasEntityPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response, error_response
from api.core.viewsets import StandardViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter


@extend_schema_view(
    list=extend_schema(
        summary="List Observable-MITRE Mappings",
        description="Returns a list of mappings between observables and MITRE ATT&CK techniques.",
        tags=["MITRE Framework"]
    ),
    retrieve=extend_schema(
        summary="Retrieve Observable-MITRE Mapping",
        description="Returns details of a specific mapping between an observable and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    create=extend_schema(
        summary="Create Observable-MITRE Mapping",
        description="Maps an observable to a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    update=extend_schema(
        summary="Update Observable-MITRE Mapping",
        description="Updates an existing mapping between an observable and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    partial_update=extend_schema(
        summary="Partially Update Observable-MITRE Mapping",
        description="Partially updates an existing mapping between an observable and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    destroy=extend_schema(
        summary="Delete Observable-MITRE Mapping",
        description="Removes a mapping between an observable and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    )
)
class ObservableMitreMappingView(StandardViewSet):
    """
    API endpoint for managing mappings between Observables and MITRE ATT&CK Techniques.
    
    This endpoint allows users to map observables (IOCs) to MITRE ATT&CK techniques,
    either manually or through automatic detection by SentinelVision analyzers.
    These mappings help in understanding the tactics and techniques associated with
    specific indicators of compromise.
    """
    queryset = ObservableMitreMapping.objects.all()
    serializer_class = ObservableMitreMappingSerializer
    permission_classes = [HasEntityPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['observable', 'technique', 'auto_detected', 'confidence']
    search_fields = ['observable__value', 'technique__name', 'technique__external_id']
    ordering_fields = ['created_at', 'confidence']
    ordering = ['-created_at']
    entity_type = 'observablemitremapping'
    
    # Success messages for standardized responses
    success_message_create = "Observable-MITRE mapping created successfully"
    success_message_update = "Observable-MITRE mapping updated successfully"
    success_message_delete = "Observable-MITRE mapping deleted successfully"
    
    def get_queryset(self):
        """
        Filter mappings by tenant isolation
        """
        queryset = super().get_queryset()
        
        # Apply tenant isolation - only show mappings for observables in the user's company
        if not self.request.user.is_superuser:
            return queryset.filter(observable__company=self.request.user.company)
            
        return queryset
    
    @extend_schema(
        summary="Bulk delete mappings",
        description="Delete all MITRE mappings for a specific observable",
        parameters=[OpenApiParameter(
            name="observable_id",
            location=OpenApiParameter.QUERY,
            required=True,
            description="UUID of the observable to delete mappings for (UUID format)",
            type=str
        )],
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
        # Validate query parameters
        serializer = ObservableMitreMappingQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(
                message="Invalid parameters",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        observable_id = serializer.validated_data['observable_id']
            
        # Apply tenant isolation
        if not request.user.is_superuser:
            mappings = self.queryset.filter(
                observable_id=observable_id, 
                observable__company=request.user.company
            )
        else:
            mappings = self.queryset.filter(observable_id=observable_id)
        
        count = mappings.count()
        mappings.delete()
        
        return success_response(
            data={'deleted_count': count},
            message=f"Successfully deleted {count} mappings"
        ) 