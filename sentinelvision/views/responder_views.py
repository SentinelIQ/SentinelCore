from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from api.core.viewsets import StandardViewSet
from api.core.rbac import HasEntityPermission
from sentinelvision.responders.block_ip import BlockIPResponder


@extend_schema_view(
    list=extend_schema(tags=['SentinelVision Responders']),
    retrieve=extend_schema(tags=['SentinelVision Responders']),
    create=extend_schema(tags=['SentinelVision Responders']),
    update=extend_schema(tags=['SentinelVision Responders']),
    partial_update=extend_schema(tags=['SentinelVision Responders']),
    destroy=extend_schema(tags=['SentinelVision Responders']),
)
class ResponderViewSet(StandardViewSet):
    """
    ViewSet for viewing and editing responders.
    """
    queryset = BlockIPResponder.objects.all()
    permission_classes = [permissions.IsAuthenticated, HasEntityPermission]
    entity_type = 'responder'
    
    def get_queryset(self):
        """
        Filter queryset based on user's company.
        """
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        return self.queryset.filter(company=user.company) 