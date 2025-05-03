from tasks.models import Task


class TaskCreateViewMixin:
    """
    Mixin for creating tasks.
    """
    def perform_create(self, serializer):
        """
        Creates a task, automatically assigning the user and company.
        """
        user = self.request.user
        serializer.save(created_by=user, company=user.company) 