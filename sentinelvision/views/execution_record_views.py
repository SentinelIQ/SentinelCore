from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from api.core.viewsets import StandardViewSet
from api.core.responses import StandardResponse, success_response, error_response
from api.core.rbac import HasEntityPermission
from sentinelvision.models import ExecutionRecord
from sentinelvision.serializers import (
    ExecutionRecordSerializer,
    ExecutionRecordDetailSerializer,
    ExecutionRecordCreateSerializer
)


@extend_schema_view(
    list=extend_schema(tags=['SentinelVision Executions']),
    retrieve=extend_schema(tags=['SentinelVision Executions']),
    create=extend_schema(tags=['SentinelVision Executions']),
    update=extend_schema(tags=['SentinelVision Executions']),
    partial_update=extend_schema(tags=['SentinelVision Executions']),
    destroy=extend_schema(tags=['SentinelVision Executions']),
)
class ExecutionRecordViewSet(StandardViewSet):
    """
    ViewSet for viewing and editing execution records.
    """
    queryset = ExecutionRecord.objects.all()
    serializer_class = ExecutionRecordSerializer
    permission_classes = [permissions.IsAuthenticated, HasEntityPermission]
    entity_type = 'execution'
    filterset_fields = ['module_name', 'module_type', 'status', 'company', 'incident', 'alert']
    search_fields = ['module_name', 'logs']
    ordering_fields = ['started_at', 'completed_at', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter queryset based on user's company.
        """
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        return self.queryset.filter(company=user.company)
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'retrieve':
            return ExecutionRecordDetailSerializer
        elif self.action == 'create':
            return ExecutionRecordCreateSerializer
        return self.serializer_class
    
    @extend_schema(
        tags=['SentinelVision Executions'],
        description="Retry a failed execution"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, HasEntityPermission])
    def retry(self, request, pk=None):
        """
        Retry a failed execution.
        """
        execution_record = self.get_object()
        
        # Check if execution is in a state that can be retried
        if execution_record.status not in [ExecutionRecord.ExecutionStatus.FAILURE, ExecutionRecord.ExecutionStatus.SKIPPED]:
            return error_response(
                message="Only failed or skipped executions can be retried",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Logic to retry the execution would go here
        
        return success_response(
            data=ExecutionRecordDetailSerializer(execution_record).data,
            message=f"Execution {execution_record.id} has been queued for retry"
        ) 