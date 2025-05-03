from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from api.core.pagination import StandardResultsSetPagination
from api.core.viewsets import UpdateModelMixin, DestroyModelMixin
from ..serializers import UserSerializer
from ..filters import UserFilter
from ..permissions import UserPermission
from drf_spectacular.utils import extend_schema

from .user_create import UserCreateMixin
from .user_detail import UserDetailMixin
from .user_custom_actions import UserCustomActionsMixin
from .token import CustomTokenObtainPairView, CustomTokenRefreshView, EmailPasswordTokenObtainView

User = get_user_model()


@extend_schema(tags=['Users'])
class UserViewSet(
    UserCreateMixin,
    UserDetailMixin,
    UserCustomActionsMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    API endpoint for user management.
    
    Users represent system accounts with different permission levels.
    Each user belongs to a specific company and has role-based access.
    """
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [UserPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['username']
    entity_type = 'user'  # Define entity type for RBAC

__all__ = [
    'UserViewSet',
    'CustomTokenObtainPairView',
    'CustomTokenRefreshView',
    'EmailPasswordTokenObtainView',
]
