from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from mitre.models import MitreTactic
from api.v1.mitre.serializers import MitreTacticSerializer, MitreTacticDetailSerializer
from api.core.rbac import HasEntityPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.viewsets import ReadOnlyViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    list=extend_schema(
        summary="List MITRE ATT&CK Tactics",
        description="Returns a list of MITRE ATT&CK Tactics.",
        tags=["MITRE ATT&CK"]
    ),
    retrieve=extend_schema(
        summary="Retrieve MITRE ATT&CK Tactic",
        description="Returns details of a specific MITRE ATT&CK Tactic.",
        tags=["MITRE ATT&CK"]
    )
)
class MitreTacticView(ReadOnlyViewSet):
    """
    API endpoint for viewing MITRE ATT&CK Tactics.
    
    This endpoint provides read-only access to the MITRE ATT&CK Tactics,
    which represent the tactical goals that adversaries try to achieve.
    """
    queryset = MitreTactic.objects.all()
    permission_classes = [HasEntityPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['external_id']
    search_fields = ['name', 'external_id', 'description']
    ordering_fields = ['name', 'external_id']
    ordering = ['external_id']
    entity_type = 'mitretactic'
    
    def get_serializer_class(self):
        """Use detailed serializer for single item, basic serializer for list"""
        if self.action == 'retrieve':
            return MitreTacticDetailSerializer
        return MitreTacticSerializer 