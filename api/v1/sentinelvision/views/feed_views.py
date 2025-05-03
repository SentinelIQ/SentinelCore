from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

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
        tags=['sentinelvision', 'feeds'],
        description='Run a feed module manually.',
        responses={
            200: OpenApiParameter(name='task_id', description='Celery task ID'),
            404: StandardResponse(status_type='error', message='Feed not found'),
            403: StandardResponse(status_type='error', message='Permission denied')
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
        tags=['sentinelvision', 'feeds'],
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