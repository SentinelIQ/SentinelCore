from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from api.core.viewsets import StandardViewSet
from api.core.rbac import HasEntityPermission
from sentinelvision.analyzers.virustotal import VirusTotalAnalyzer


@extend_schema_view(
    list=extend_schema(tags=['SentinelVision Analyzers']),
    retrieve=extend_schema(tags=['SentinelVision Analyzers']),
    create=extend_schema(tags=['SentinelVision Analyzers']),
    update=extend_schema(tags=['SentinelVision Analyzers']),
    partial_update=extend_schema(tags=['SentinelVision Analyzers']),
    destroy=extend_schema(tags=['SentinelVision Analyzers']),
)
class AnalyzerViewSet(StandardViewSet):
    """
    ViewSet for viewing and editing analyzers.
    """
    queryset = VirusTotalAnalyzer.objects.all()
    permission_classes = [permissions.IsAuthenticated, HasEntityPermission]
    entity_type = 'analyzer'
    
    def get_queryset(self):
        """
        Filter queryset based on user's company.
        """
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        return self.queryset.filter(company=user.company) 