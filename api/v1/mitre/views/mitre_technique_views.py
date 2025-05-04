from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import CharFilter, FilterSet
from django.db.models import Count
from django.contrib.postgres.fields import ArrayField
from mitre.models import MitreTechnique
from api.v1.mitre.serializers import MitreTechniqueSerializer, MitreTechniqueDetailSerializer
from api.core.rbac import HasEntityPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response
from api.core.viewsets import ReadOnlyViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view


class MitreTechniqueFilter(FilterSet):
    """
    Custom filter for MitreTechnique to handle ArrayField filtering
    """
    platforms = CharFilter(method='filter_platforms')
    
    class Meta:
        model = MitreTechnique
        fields = ['external_id', 'tactics', 'is_subtechnique', 'platforms']
        filter_overrides = {
            ArrayField: {'filter_class': CharFilter, 'extra': lambda f: {'lookup_expr': 'contains'}}
        }
    
    def filter_platforms(self, queryset, name, value):
        """Filter for array field containment"""
        if value:
            return queryset.filter(platforms__contains=[value])
        return queryset


@extend_schema_view(
    list=extend_schema(
        summary="List MITRE ATT&CK Techniques",
        description="Returns a list of MITRE ATT&CK Techniques.",
        tags=["MITRE Framework"]
    ),
    retrieve=extend_schema(
        summary="Retrieve MITRE ATT&CK Technique",
        description="Returns details of a specific MITRE ATT&CK Technique.",
        tags=["MITRE Framework"]
    ),
    related_entities=extend_schema(
        summary="Get entities related to this MITRE Technique",
        description="Returns counts of alerts, incidents, and observables linked to this technique.",
        tags=["MITRE Framework"]
    ),
    subtechniques=extend_schema(
        summary="Get subtechniques of this MITRE Technique",
        description="Returns a list of subtechniques for this parent technique.",
        tags=["MITRE Framework"]
    )
)
class MitreTechniqueView(ReadOnlyViewSet):
    """
    API endpoint for viewing MITRE ATT&CK Techniques.
    
    This endpoint provides read-only access to the MITRE ATT&CK Techniques,
    which represent the tactics, techniques, and procedures that adversaries use.
    """
    queryset = MitreTechnique.objects.all()
    permission_classes = [HasEntityPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MitreTechniqueFilter
    search_fields = ['name', 'external_id', 'description']
    ordering_fields = ['name', 'external_id']
    ordering = ['external_id']
    entity_type = 'mitretechnique'
    
    def get_serializer_class(self):
        """Use detailed serializer for single item, basic serializer for list"""
        if self.action == 'retrieve':
            return MitreTechniqueDetailSerializer
        return MitreTechniqueSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about techniques"""
        # Count techniques by tactic
        tactic_counts = (
            MitreTechnique.objects
            .values('tactics__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Count subtechniques vs techniques
        type_counts = {
            'techniques': MitreTechnique.objects.filter(is_subtechnique=False).count(),
            'subtechniques': MitreTechnique.objects.filter(is_subtechnique=True).count()
        }
        
        # Count by platform
        platform_counts = {}
        for technique in MitreTechnique.objects.all():
            for platform in technique.platforms:
                if platform not in platform_counts:
                    platform_counts[platform] = 0
                platform_counts[platform] += 1
        
        # Sort platform counts
        sorted_platforms = [
            {'platform': k, 'count': v}
            for k, v in sorted(platform_counts.items(), key=lambda item: item[1], reverse=True)
        ]
        
        data = {
            'by_tactic': list(tactic_counts),
            'by_type': type_counts,
            'by_platform': sorted_platforms
        }
        
        return success_response(data=data)
    
    @action(detail=True, methods=['get'])
    def related_entities(self, request, pk=None):
        """Get counts of entities related to this technique"""
        technique = self.get_object()
        alert_count = technique.alerts.count()
        incident_count = technique.incidents.count()
        observable_count = technique.observables.count()
        
        data = {
            'alert_count': alert_count,
            'incident_count': incident_count,
            'observable_count': observable_count,
        }
        
        return success_response(data=data)
    
    @action(detail=True, methods=['get'])
    def subtechniques(self, request, pk=None):
        """Get subtechniques for this technique"""
        technique = self.get_object()
        subtechniques = technique.subtechniques.all()
        page = self.paginate_queryset(subtechniques)
        
        if page is not None:
            serializer = MitreTechniqueSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = MitreTechniqueSerializer(subtechniques, many=True)
        return success_response(data=serializer.data) 