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
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample


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
        description=(
            "Retrieves a comprehensive list of MITRE ATT&CK Techniques with filtering capabilities. "
            "MITRE ATT&CK is a globally-accessible knowledge base of adversary tactics and techniques "
            "based on real-world observations. The techniques represent the various methods that adversaries "
            "use to accomplish tactical goals during an attack. This endpoint supports security operations "
            "by providing standardized technique definitions that can be mapped to detection rules, "
            "security controls, and threat intelligence. The list can be filtered by various criteria "
            "including tactic, platform, and whether it's a subtechnique."
        ),
        responses={
            200: OpenApiResponse(
                description="Techniques retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="techniques_list",
                        summary="Techniques list example",
                        description="Example showing a paginated list of MITRE ATT&CK techniques",
                        value={
                            "count": 586,
                            "next": "https://api.example.com/api/v1/mitre/techniques/?page=2",
                            "previous": None,
                            "results": [
                                {
                                    "id": "f3221f77-f3f1-458d-98a1-26a9d8d33b8a",
                                    "external_id": "T1059",
                                    "name": "Command and Scripting Interpreter",
                                    "description": "Adversaries may abuse command and script interpreters to execute commands...",
                                    "is_subtechnique": False,
                                    "platforms": ["Windows", "macOS", "Linux"],
                                    "tactics": [
                                        {
                                            "id": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                                            "name": "Execution",
                                            "external_id": "TA0002"
                                        }
                                    ]
                                }
                            ]
                        }
                    )
                ]
            )
        },
        tags=["MITRE Framework"]
    ),
    retrieve=extend_schema(
        summary="Retrieve MITRE ATT&CK Technique",
        description=(
            "Retrieves detailed information about a specific MITRE ATT&CK Technique, including its full "
            "description, platforms it affects, associated tactics, mitigations, and related techniques. "
            "This endpoint provides the comprehensive knowledge needed for threat modeling, security control "
            "development, and detection strategy creation. The detailed technique information helps security "
            "teams understand attacker methodologies and implement appropriate countermeasures. For subtechniques, "
            "the parent technique is also included to show the hierarchical relationship."
        ),
        responses={
            200: OpenApiResponse(
                description="Technique retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="technique_detail",
                        summary="Technique detail example",
                        description="Example showing detailed information for T1566 (Phishing)",
                        value={
                            "id": "c5e8d873-cf00-45c7-a9e4-86f9f9a3c321",
                            "external_id": "T1566",
                            "name": "Phishing",
                            "description": "Adversaries may send phishing messages to gain access to victim systems...",
                            "is_subtechnique": False,
                            "platforms": ["Windows", "macOS", "Linux", "Office 365", "SaaS"],
                            "data_sources": ["Network Traffic", "Email Gateway", "User Interface"],
                            "detection": "Monitor for suspicious email attachments and URLs...",
                            "tactics": [
                                {
                                    "id": "7c637454-d1e9-4763-9aa8-c1050e07ad10",
                                    "name": "Initial Access",
                                    "external_id": "TA0001"
                                }
                            ],
                            "mitigations": [
                                {
                                    "id": "2f042a9f-e9d2-445b-9ec8-5d8b4739c543",
                                    "name": "User Training",
                                    "external_id": "M1017",
                                    "description": "Train users to identify social engineering techniques..."
                                }
                            ],
                            "created": "2020-01-15T12:30:00Z",
                            "modified": "2022-03-27T09:45:00Z",
                            "subtechniques_count": 3
                        }
                    )
                ]
            )
        },
        tags=["MITRE Framework"]
    ),
    related_entities=extend_schema(
        summary="Get entities related to this MITRE Technique",
        description=(
            "Retrieves counts of security entities (alerts, incidents, and observables) that are linked to "
            "this MITRE ATT&CK technique. This endpoint is essential for threat hunting and security operations, "
            "allowing analysts to identify how frequently a specific attack technique appears across their security "
            "data. The counts help prioritize response to techniques that are more commonly seen in the environment "
            "and provide insights into the prevalence of specific attack patterns. This information supports "
            "better allocation of security resources and more targeted defensive measures."
        ),
        responses={
            200: OpenApiResponse(
                description="Related entity counts retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="technique_relationships",
                        summary="Related entity counts example",
                        description="Example showing counts of entities related to T1566 (Phishing)",
                        value={
                            "status": "success",
                            "message": "Data retrieved successfully",
                            "data": {
                                "alert_count": 147,
                                "incident_count": 38,
                                "observable_count": 215
                            }
                        }
                    )
                ]
            )
        },
        tags=["MITRE Framework"]
    ),
    subtechniques=extend_schema(
        summary="Get subtechniques of this MITRE Technique",
        description=(
            "Retrieves all subtechniques associated with a parent MITRE ATT&CK technique. Subtechniques provide "
            "more granular descriptions of specific adversary behaviors within the context of a parent technique. "
            "This endpoint is valuable for security analysts who need to understand the various ways a particular "
            "technique can be implemented by attackers. The hierarchical relationship between techniques and "
            "subtechniques supports more precise threat modeling, detection rule development, and security control "
            "implementation. Each subtechnique includes its ATT&CK ID, name, description, and other metadata."
        ),
        responses={
            200: OpenApiResponse(
                description="Subtechniques retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="subtechniques_list",
                        summary="Subtechniques example",
                        description="Example showing subtechniques for T1059 (Command and Scripting Interpreter)",
                        value={
                            "status": "success",
                            "message": "Data retrieved successfully",
                            "data": [
                                {
                                    "id": "3f886859-c6ce-4e46-9b06-8f37a258e7c5",
                                    "external_id": "T1059.001",
                                    "name": "PowerShell",
                                    "description": "Adversaries may abuse PowerShell commands and scripts...",
                                    "is_subtechnique": True,
                                    "platforms": ["Windows"],
                                    "parent_technique": "f3221f77-f3f1-458d-98a1-26a9d8d33b8a"
                                },
                                {
                                    "id": "49efd859-5c72-4d27-af9f-8d91915dd82f",
                                    "external_id": "T1059.003",
                                    "name": "Windows Command Shell",
                                    "description": "Adversaries may abuse the Windows command shell...",
                                    "is_subtechnique": True,
                                    "platforms": ["Windows"],
                                    "parent_technique": "f3221f77-f3f1-458d-98a1-26a9d8d33b8a"
                                }
                            ]
                        }
                    )
                ]
            )
        },
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
    
    @extend_schema(
        summary="Get MITRE Technique statistics",
        description=(
            "Provides comprehensive statistics about MITRE ATT&CK techniques categorized by tactics, "
            "technique types, and platforms. This endpoint is critical for threat intelligence analysis "
            "and security posture assessments. The data returned enables security teams to understand "
            "the distribution of techniques across different tactics (like Initial Access, Execution, etc.), "
            "differentiate between base techniques and subtechniques, and identify which platforms (Windows, "
            "Linux, Cloud, etc.) have more documented attack techniques. This information helps in prioritizing "
            "security controls and detection capabilities."
        ),
        responses={
            200: OpenApiResponse(
                description="Statistics retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="technique_statistics",
                        summary="Technique statistics example",
                        description="Example showing statistics for MITRE ATT&CK techniques",
                        value={
                            "status": "success",
                            "message": "Data retrieved successfully",
                            "data": {
                                "by_tactic": [
                                    {"tactics__name": "Defense Evasion", "count": 42},
                                    {"tactics__name": "Execution", "count": 28},
                                    {"tactics__name": "Persistence", "count": 19}
                                ],
                                "by_type": {
                                    "techniques": 193,
                                    "subtechniques": 401
                                },
                                "by_platform": [
                                    {"platform": "Windows", "count": 312},
                                    {"platform": "Linux", "count": 289},
                                    {"platform": "macOS", "count": 261},
                                    {"platform": "Cloud", "count": 124}
                                ]
                            }
                        }
                    )
                ]
            )
        },
        tags=["MITRE Framework"]
    )
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