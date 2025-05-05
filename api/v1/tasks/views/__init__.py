from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from tasks.models import Task
from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response
from api.core.rbac import HasEntityPermission
from api.core.viewsets import StandardViewSet
from api.core.audit import AuditLogMixin
from drf_spectacular.utils import extend_schema, extend_schema_view
from ..serializers import TaskSerializer

from .task_detail import TaskDetailViewMixin
from .task_create import TaskCreateViewMixin
from .task_custom_actions import TaskCustomActionsMixin


@extend_schema_view(
    list=extend_schema(
        tags=['Task Management'],
        summary="List all tasks",
        description="Get a paginated list of all tasks for the current user's company."
    ),
    retrieve=extend_schema(
        tags=['Task Management'],
        summary="Get task detail",
        description="Retrieve detailed information about a specific task."
    ),
    create=extend_schema(
        tags=['Task Management'],
        summary="Create a new task",
        description="Create a new task with the provided data."
    ),
    update=extend_schema(
        tags=['Task Management'],
        summary="Update a task",
        description="Update all fields of an existing task."
    ),
    partial_update=extend_schema(
        tags=['Task Management'],
        summary="Partially update a task",
        description="Update specific fields of an existing task."
    ),
    destroy=extend_schema(
        tags=['Task Management'],
        summary="Delete a task",
        description="Permanently delete a task."
    )
)
@extend_schema(tags=['Task Management'])
class TaskViewSet(
    AuditLogMixin,
    TaskDetailViewMixin,
    TaskCreateViewMixin,
    TaskCustomActionsMixin,
    StandardViewSet
):
    """
    API endpoint for task management.
    
    Tasks represent actions to be completed as part of incident investigation.
    Each task belongs to a specific incident and can be assigned to a user.
    """
    entity_type = 'task'  # Define entity type for RBAC and audit logging
    
    # Success messages for standardized responses
    success_message_create = "Task created successfully"
    success_message_update = "Task updated successfully"
    success_message_delete = "Task deleted successfully"
    
    def get_additional_log_data(self, request, obj=None, action=None):
        """
        Customize audit log data for tasks.
        
        Add task-specific fields to the audit log, such as status,
        priority, and associated incident.
        
        Args:
            request: The HTTP request
            obj: The task object being acted upon
            action: The action being performed (create, update, delete)
            
        Returns:
            dict: Additional data for the audit log
        """
        # Get standard log data from parent class
        data = super().get_additional_log_data(request, obj, action)
        
        # Add task-specific data
        if obj:
            data.update({
                'task_title': getattr(obj, 'title', None),
                'task_status': getattr(obj, 'status', None),
                'task_priority': getattr(obj, 'priority', None),
                'incident_id': str(obj.incident.id) if getattr(obj, 'incident', None) else None,
                'company_id': str(obj.company.id) if getattr(obj, 'company', None) else None,
            })
            
        return data


__all__ = [
    'TaskViewSet',
] 