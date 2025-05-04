from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from tasks.models import Task
from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response
from api.core.rbac import HasEntityPermission
from api.core.viewsets import StandardViewSet
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
    entity_type = 'task'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Task created successfully"
    success_message_update = "Task updated successfully"
    success_message_delete = "Task deleted successfully"


__all__ = [
    'TaskViewSet',
] 