from rest_framework import filters, status
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from mitre.models import IncidentMitreMapping
from api.v1.mitre.serializers import IncidentMitreMappingSerializer
from api.core.rbac import HasEntityPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response, error_response
from api.core.viewsets import StandardViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    list=extend_schema(
        summary="List Incident-MITRE Mappings",
        description="Returns a list of mappings between incidents and MITRE ATT&CK techniques.",
        tags=["MITRE Framework"]
    ),
    retrieve=extend_schema(
        summary="Retrieve Incident-MITRE Mapping",
        description="Returns details of a specific mapping between an incident and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    create=extend_schema(
        summary="Create Incident-MITRE Mapping",
        description="Maps an incident to a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    update=extend_schema(
        summary="Update Incident-MITRE Mapping",
        description="Updates an existing mapping between an incident and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    partial_update=extend_schema(
        summary="Partially Update Incident-MITRE Mapping",
        description="Partially updates an existing mapping between an incident and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    ),
    destroy=extend_schema(
        summary="Delete Incident-MITRE Mapping",
        description="Removes a mapping between an incident and a MITRE ATT&CK technique.",
        tags=["MITRE Framework"]
    )
)
class IncidentMitreMappingView(StandardViewSet):
    """
    API endpoint for managing mappings between Incidents and MITRE ATT&CK Techniques.
    
    This endpoint allows security analysts to map incidents to MITRE ATT&CK techniques
    to better document the tactics and techniques used in security incidents.
    These mappings are typically added manually during incident investigation.
    """
    queryset = IncidentMitreMapping.objects.all()
    serializer_class = IncidentMitreMappingSerializer
    permission_classes = [HasEntityPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['incident', 'technique', 'confidence']
    search_fields = ['incident__title', 'technique__name', 'technique__external_id', 'notes']
    ordering_fields = ['created_at', 'confidence']
    ordering = ['-created_at']
    entity_type = 'incidentmitremapping'
    
    # Success messages for standardized responses
    success_message_create = "Incident-MITRE mapping created successfully"
    success_message_update = "Incident-MITRE mapping updated successfully"
    success_message_delete = "Incident-MITRE mapping deleted successfully"
    
    def get_queryset(self):
        """
        Filter mappings by tenant isolation
        """
        queryset = super().get_queryset()
        
        # Apply tenant isolation - only show mappings for incidents in the user's company
        if not self.request.user.is_superuser:
            return queryset.filter(incident__company=self.request.user.company)
            
        return queryset
    
    @extend_schema(
        summary="Bulk delete mappings",
        description="Delete all MITRE mappings for a specific incident",
        parameters=[
            {
                "name": "incident_id",
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
        incident_id = request.query_params.get('incident_id')
        if not incident_id:
            return error_response("Incident ID is required", status_code=status.HTTP_400_BAD_REQUEST)
            
        # Apply tenant isolation
        if not request.user.is_superuser:
            mappings = self.queryset.filter(
                incident_id=incident_id, 
                incident__company=request.user.company
            )
        else:
            mappings = self.queryset.filter(incident_id=incident_id)
        
        count = mappings.count()
        mappings.delete()
        
        return success_response(
            data={'deleted_count': count},
            message=f"Successfully deleted {count} mappings"
        ) 