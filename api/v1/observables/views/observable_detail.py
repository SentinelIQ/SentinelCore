from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from observables.models import Observable
from api.core.pagination import StandardResultsSetPagination
from api.core.rbac import HasEntityPermission
from ..serializers import (
    ObservableSerializer,
    ObservableDetailSerializer,
    ObservableCreateSerializer,
    ObservableHistorySerializer
)
from ..filters import ObservableFilter
import logging

logger = logging.getLogger('api.observables')


class ObservableDetailViewMixin:
    """
    Mixin for Observable detail operations (list, retrieve).
    """
    serializer_class = ObservableSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [HasEntityPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['value', 'description', 'type']
    ordering_fields = ['created_at', 'updated_at', 'type', 'is_ioc']
    ordering = ['-created_at']
    filterset_class = ObservableFilter
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'retrieve':
            return ObservableDetailSerializer
        elif self.action == 'create':
            return ObservableCreateSerializer
        elif self.action == 'history':
            return ObservableHistorySerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Returns only observables from the user's company, unless the user is a superuser.
        """
        user = self.request.user
        
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for OpenAPI schema generation
            return Observable.objects.none()
        
        if user.is_superuser:
            return Observable.objects.all()
        
        return Observable.objects.filter(company=user.company) 