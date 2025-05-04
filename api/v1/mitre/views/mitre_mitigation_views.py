from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from mitre.models import MitreMitigation
from api.v1.mitre.serializers import MitreMitigationSerializer, MitreMitigationDetailSerializer
from api.core.rbac import HasEntityPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.viewsets import ReadOnlyViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    list=extend_schema(
        summary="List MITRE ATT&CK Mitigations",
        description="Returns a list of MITRE ATT&CK Mitigations.",
        tags=["MITRE Framework"]
    ),
    retrieve=extend_schema(
        summary="Retrieve MITRE ATT&CK Mitigation",
        description="Returns details of a specific MITRE ATT&CK Mitigation.",
        tags=["MITRE Framework"]
    )
)
class MitreMitigationView(ReadOnlyViewSet):
    """
    API endpoint for viewing MITRE ATT&CK Mitigations.
    
    This endpoint provides read-only access to the MITRE ATT&CK Mitigations,
    which represent security measures that can be taken to prevent or counter attacks.
    """
    queryset = MitreMitigation.objects.all()
    permission_classes = [HasEntityPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['external_id']
    search_fields = ['name', 'external_id', 'description']
    ordering_fields = ['name', 'external_id']
    ordering = ['external_id']
    entity_type = 'mitremitigation'
    
    def get_serializer_class(self):
        """Use detailed serializer for single item, basic serializer for list"""
        if self.action == 'retrieve':
            return MitreMitigationDetailSerializer
        return MitreMitigationSerializer 