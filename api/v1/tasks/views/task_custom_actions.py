from rest_framework.decorators import action
from rest_framework import status
from api.core.responses import success_response
from drf_spectacular.utils import extend_schema
from ..serializers import TaskSerializer


class TaskCustomActionsMixin:
    """
    Mixin for custom task actions.
    """
    @extend_schema(
        summary="Mark task as completed",
        description="Mark a task as completed and update the incident timeline",
        responses={200: TaskSerializer}
    )
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_task(self, request, pk=None):
        """
        Mark a task as completed and add an entry to the incident timeline.
        """
        task = self.get_object()
        task.mark_completed(user=request.user)
        
        return success_response(
            data=TaskSerializer(task).data,
            message="Task marked as completed",
            status_code=status.HTTP_200_OK
        ) 