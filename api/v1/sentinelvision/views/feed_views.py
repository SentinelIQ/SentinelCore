from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from api.core.responses import (
    success_response, error_response, StandardResponse
)
from sentinelvision.models import (
    FeedModule, FeedExecutionRecord, 
    ExecutionSourceEnum, ExecutionStatusEnum
)
from sentinelvision.permissions import CanExecuteFeedPermission, IsSuperuserPermission
from api.v1.sentinelvision.serializers import (
    FeedModuleSerializer, FeedExecutionRecordSerializer, FeedModuleListSerializer
)
from sentinelvision.tasks import run_feed_task

@extend_schema(tags=['Threat Intelligence (SentinelVision)'])
class FeedModuleViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing and executing feed modules.
    """
    queryset = FeedModule.objects.all()
    serializer_class = FeedModuleSerializer
    permission_classes = [CanExecuteFeedPermission]
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions:
        - Superusers can see all feeds
        - Regular users can only see feeds linked to their company
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_superuser:
            # Regular users can only see feeds linked to their company
            queryset = queryset.filter(company=user.company)
            
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return FeedModuleListSerializer
        return FeedModuleSerializer
    
    @extend_schema(
        tags=['Threat Intelligence (SentinelVision)'],
        summary="Execute threat intelligence feed processing",
        description=(
            "Manually triggers the execution of a threat intelligence feed module. This endpoint initiates "
            "the asynchronous collection and processing of security data from external sources through the "
            "SentinelVision automation engine. Feed modules are responsible for ingesting threat intelligence "
            "data such as malicious indicators, threat actor details, and vulnerability information. The execution "
            "creates a record in the system and tracks the processing status. This capability is essential for "
            "security operations to update intelligence data on-demand rather than waiting for scheduled runs, "
            "particularly when responding to emerging threats that require immediate intelligence updates."
        ),
        responses={
            200: OpenApiResponse(
                description="Feed execution started successfully",
                examples=[
                    OpenApiExample(
                        name="feed_execution_response",
                        summary="Feed execution initiated",
                        description="Example of a successful feed execution request response",
                        value={
                            "status": "success",
                            "message": "Feed 'MISP Community Feed' execution started. Check history for status.",
                            "data": {
                                "execution_id": "f2a05b4c-7c1d-4a9e-8e5f-3e9a1b2c3d4e",
                                "task_id": "8eca7b3d-5f9a-4b2c-a1e3-7d8c9f0a1b2c",
                                "feed_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
                                "feed_name": "MISP Community Feed",
                                "started_at": "2023-05-15T14:30:45.123456Z"
                            }
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Feed not found",
                examples=[
                    OpenApiExample(
                        name="feed_not_found",
                        summary="Feed not found error",
                        description="Example of response when the specified feed doesn't exist",
                        value={
                            "status": "error",
                            "message": "Feed not found",
                            "data": None
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied error",
                        description="Example of response when user lacks permission to execute the feed",
                        value={
                            "status": "error",
                            "message": "You do not have permission to execute this feed",
                            "data": None
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['post'], url_path='run')
    def run_feed(self, request, pk=None):
        """
        Manually run a feed module.
        Creates a FeedExecutionRecord and triggers a Celery task.
        """
        feed = self.get_object()
        
        # Create execution record
        execution_record = FeedExecutionRecord.objects.create(
            feed=feed,
            executed_by=request.user,
            source=ExecutionSourceEnum.MANUAL,
            status=ExecutionStatusEnum.PENDING,
            started_at=timezone.now()
        )
        
        # Run feed task asynchronously
        task = run_feed_task.delay(
            feed_id=str(feed.id),
            execution_record_id=str(execution_record.id),
            company_id=str(feed.company.id) if feed.company else None
        )
        
        return success_response(
            message=f"Feed '{feed.name}' execution started. Check history for status.",
            data={
                'execution_id': str(execution_record.id),
                'task_id': task.id,
                'feed_id': str(feed.id),
                'feed_name': feed.name,
                'started_at': execution_record.started_at.isoformat()
            }
        )
    
    @extend_schema(
        tags=['Threat Intelligence (SentinelVision)'],
        description='List execution history for a feed module.',
        responses={
            200: FeedExecutionRecordSerializer(many=True),
            404: StandardResponse(status_type='error', message='Feed not found'),
            403: StandardResponse(status_type='error', message='Permission denied')
        }
    )
    @action(detail=True, methods=['get'], url_path='history')
    def execution_history(self, request, pk=None):
        """
        Get execution history for a feed module.
        Returns a list of FeedExecutionRecord objects.
        """
        feed = self.get_object()
        
        # Get all execution records for this feed, ordered by started_at desc
        execution_records = FeedExecutionRecord.objects.filter(
            feed=feed
        ).select_related('executed_by').order_by('-started_at')
        
        # Paginate and serialize results
        page = self.paginate_queryset(execution_records)
        if page is not None:
            serializer = FeedExecutionRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = FeedExecutionRecordSerializer(execution_records, many=True)
        return success_response(
            message=f"Execution history for feed '{feed.name}'.",
            data=serializer.data
        ) 