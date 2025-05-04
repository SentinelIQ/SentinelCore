from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from api.core.viewsets import StandardViewSet
from api.core.rbac import HasEntityPermission
from sentinelvision.analyzers.virustotal import VirusTotalAnalyzer


@extend_schema_view(
    list=extend_schema(tags=['Threat Intelligence (SentinelVision)']),
 extend_schema(tags=['Threat Intelligence (SentinelVision)'] Aextend_schema(tags=['Threat Intelligence (SentinelVision)']ntextend_schema(tags=['Threat Intelligence (SentinelVision)']ma(tags=['extend_schema(tags=['Threat Intelligence (SentinelVision)']=exextend_schema(tags=['Threat Intelligence (SentinelVision)']
    destroy=extend_schema(tags=['Threat Intelligence (SentinelVision)']),
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