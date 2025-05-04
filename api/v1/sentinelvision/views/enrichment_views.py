from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from api.core.responses import (
    success_response, error_response, StandardResponse
)
from sentinelvision.models import (
    EnrichedIOC, IOCFeedMatch, IOCTypeEnum, EnrichmentStatusEnum
)
from api.v1.sentinelvision.serializers import (
    EnrichedIOCSerializer, IOCFeedMatchSerializer,
    EnrichObservableRequestSerializer
)
from sentinelvision.permissions import CanExecuteFeedPermission
from sentinelvision.tasks.enrichment_tasks import enrich_observable

@extend_schema(tags=['Threat Intelligence (SentinelVision)'])
class EnrichmentViewSet(viewsets.ViewSet):
    """
    API endpoints for enriching and managing observables (IOCs).
    """
    permission_classes = [CanExecuteFeedPermission]
    
    @extend_schema(
        tags=['Threat Intelligence (SentinelVision)'],
        description='Enrich an observable (IOC) by checking it against all relevant feeds.',
        request=EnrichObservableRequestSerializer,
        responses={
            200: StandardResponse(status_type='success'),
            400: StandardResponse(status_type='error', message='Invalid request'),
            403: StandardResponse(status_type='error', message='Permission denied')
        },
        examples=[
            OpenApiExample(
                'IP Enrichment',
                summary='Enrich an IP address',
                value={
                    'ioc_type': 'ip',
                    'ioc_value': '1.2.3.4',
                    'description': 'Suspicious IP from alert'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Domain Enrichment',
                summary='Enrich a domain',
                value={
                    'ioc_type': 'domain',
                    'ioc_value': 'malicious.example.com',
                    'description': 'Suspicious domain from email'
                },
                request_only=True,
            )
        ]
    )
    @action(detail=False, methods=['post'], url_path='enrich-observable')
    def enrich_observable(self, request):
        """
        Enrich an observable (IOC) by checking it against all relevant feeds.
        This is an asynchronous operation that will return a task ID.
        """
        # Validate request
        serializer = EnrichObservableRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid request parameters",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract validated data
        ioc_type = serializer.validated_data['ioc_type']
        ioc_value = serializer.validated_data['ioc_value']
        description = serializer.validated_data.get('description', '')
        
        # Get company from user
        company = request.user.company
        
        # Check if this IOC already exists for this company
        existing_ioc = EnrichedIOC.objects.filter(
            company=company,
            ioc_type=ioc_type,
            value=ioc_value
        ).first()
        
        if existing_ioc and existing_ioc.is_enriched:
            # Return existing enrichment data
            serializer = EnrichedIOCSerializer(existing_ioc)
            return success_response(
                message=f"Observable already enriched",
                data={
                    'ioc': serializer.data,
                    'status': 'already_enriched'
                }
            )
        
        # Launch enrichment task
        task = enrich_observable.delay(
            company_id=str(company.id),
            ioc_type=ioc_type,
            ioc_value=ioc_value,
            source='api',
            description=description
        )
        
        return success_response(
            message=f"Enrichment task for {ioc_type}: {ioc_value} started",
            data={
                'task_id': task.id,
                'ioc_type': ioc_type,
                'ioc_value': ioc_value,
                'status': 'pending'
            }
        )
    
    @extend_schema(
        tags=['Threat Intelligence (SentinelVision)'],
        description='List enriched observables (IOCs) for the current company.',
        responses={
            200: EnrichedIOCSerializer(many=True),
            403: StandardResponse(status_type='error', message='Permission denied')
        },
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by enrichment status',
                required=False,
                type=str,
                enum=['pending', 'enriched', 'not_found']
            ),
            OpenApiParameter(
                name='ioc_type',
                description='Filter by IOC type',
                required=False,
                type=str,
                enum=[choice[0] for choice in IOCTypeEnum.choices]
            ),
            OpenApiParameter(
                name='value',
                description='Search by IOC value',
                required=False,
                type=str
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='list-observables')
    def list_observables(self, request):
        """
        List enriched observables (IOCs) for the current company.
        """
        # Get company from user
        company = request.user.company
        
        # Build queryset with filters
        queryset = EnrichedIOC.objects.filter(company=company)
        
        # Apply filters
        status = request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        ioc_type = request.query_params.get('ioc_type')
        if ioc_type:
            queryset = queryset.filter(ioc_type=ioc_type)
            
        value = request.query_params.get('value')
        if value:
            queryset = queryset.filter(value__icontains=value)
        
        # Order by last checked (newest first)
        queryset = queryset.order_by('-last_checked')
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EnrichedIOCSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        # If no pagination, serialize all results
        serializer = EnrichedIOCSerializer(queryset, many=True)
        
        return success_response(
            message=f"Found {queryset.count()} enriched observables",
            data=serializer.data
        )
    
    @extend_schema(
        tags=['Threat Intelligence (SentinelVision)'],
        description='Get details of a specific enriched observable (IOC).',
        responses={
            200: EnrichedIOCSerializer(),
            404: StandardResponse(status_type='error', message='Observable not found'),
            403: StandardResponse(status_type='error', message='Permission denied')
        }
    )
    @action(detail=True, methods=['get'], url_path='observable-details')
    def observable_details(self, request, pk=None):
        """
        Get details of a specific enriched observable (IOC).
        """
        # Get company from user
        company = request.user.company
        
        # Get the IOC
        ioc = get_object_or_404(EnrichedIOC, id=pk, company=company)
        
        # Serialize with feed matches
        serializer = EnrichedIOCSerializer(ioc)
        
        return success_response(
            message=f"Details for {ioc.get_ioc_type_display()}: {ioc.value}",
            data=serializer.data
        )
    
    @extend_schema(
        tags=['Threat Intelligence (SentinelVision)'],
        description='Force re-enrichment of a specific observable (IOC).',
        responses={
            200: StandardResponse(status_type='success'),
            404: StandardResponse(status_type='error', message='Observable not found'),
            403: StandardResponse(status_type='error', message='Permission denied')
        }
    )
    @action(detail=True, methods=['post'], url_path='reenrich-observable')
    def reenrich_observable(self, request, pk=None):
        """
        Force re-enrichment of a specific observable (IOC).
        """
        # Get company from user
        company = request.user.company
        
        # Get the IOC
        ioc = get_object_or_404(EnrichedIOC, id=pk, company=company)
        
        # Launch enrichment task
        task = enrich_observable.delay(
            company_id=str(company.id),
            ioc_type=ioc.ioc_type,
            ioc_value=ioc.value,
            source=ioc.source,
            description=ioc.description
        )
        
        return success_response(
            message=f"Re-enrichment task for {ioc.get_ioc_type_display()}: {ioc.value} started",
            data={
                'task_id': task.id,
                'ioc_id': str(ioc.id),
                'ioc_type': ioc.ioc_type,
                'ioc_value': ioc.value,
                'status': 'pending'
            }
        )
    
    def paginate_queryset(self, queryset):
        """
        Return a single page of results or None if not paginated.
        """
        if hasattr(self, 'paginator') and self.paginator is not None:
            return self.paginator.paginate_queryset(queryset, self.request, view=self)
        return None
    
    def get_paginated_response(self, data):
        """
        Return a paginated response.
        """
        assert hasattr(self, 'paginator') and self.paginator is not None
        return self.paginator.get_paginated_response(data) 