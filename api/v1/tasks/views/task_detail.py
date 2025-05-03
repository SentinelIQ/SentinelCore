from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from tasks.models import Task
from api.core.pagination import StandardResultsSetPagination
from api.core.rbac import HasEntityPermission
from ..serializers import TaskSerializer


class TaskDetailViewMixin:
    """
    Mixin for retrieving task details.
    """
    serializer_class = TaskSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [HasEntityPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'status', 'priority', 'order']
    ordering = ['order', 'due_date', '-priority']
    filterset_fields = ['status', 'priority', 'incident', 'assigned_to']
    
    def get_queryset(self):
        """
        Returns only tasks from the user's company, unless the user is a superuser.
        """
        user = self.request.user
        
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for OpenAPI schema generation
            return Task.objects.none()
        
        if user.is_superuser:
            return Task.objects.all()
        
        return Task.objects.filter(company=user.company) 