from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from mitre.models import MitreRelationship
from api.v1.mitre.serializers import MitreRelationshipSerializer
from api.core.rbac import HasEntityPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.viewsets import ReadOnlyViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    list=extend_schema(
        summary="List MITRE ATT&CK Relationships",
        description="Returns a list of relationships between MITRE ATT&CK objects.",
        tags=["MITRE ATT&CK"]
    ),
    retrieve=extend_schema(
        summary="Retrieve MITRE ATT&CK Relationship",
        description="Returns details of a specific relationship between MITRE ATT&CK objects.",
        tags=["MITRE ATT&CK"]
    )
)
class MitreRelationshipView(ReadOnlyViewSet):
    """
    API endpoint for viewing MITRE ATT&CK Relationships.
    
    This endpoint provides read-only access to the relationships between MITRE ATT&CK objects,
    such as techniques, tactics, mitigations, and groups.
    """
    queryset = MitreRelationship.objects.all()
    permission_classes = [HasEntityPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_id', 'target_id', 'relationship_type']
    search_fields = ['source_id', 'target_id', 'relationship_type']
    ordering_fields = ['source_id', 'target_id', 'relationship_type']
    ordering = ['relationship_type']
    entity_type = 'mitrerelationship'
    serializer_class = MitreRelationshipSerializer 