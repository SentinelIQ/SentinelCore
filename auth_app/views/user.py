from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from api.core.responses import success_response
from api.permissions import IsSuperUser, IsAdminCompany, IsOwnerOrSuperUser, ReadOnly
from api.core.rbac import HasEntityPermission
from auth_app.serializers.user import UserSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema(tags=['Authentication & Access Control'])
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    entity_type = 'user'  # Define entity type for RBAC
    
    def get_queryset(self):
        """
        Filter users based on user's permissions:
        - Superuser can see all users
        - Company admin can see users of their company
        - Company analyst can only see themselves
        """
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.is_superuser:
            return queryset
        elif user.is_admin_company:
            return queryset.filter(company=user.company)
        else:
            return queryset.filter(id=user.id)
    
    def get_permissions(self):
        """
        - Superuser can perform all actions
        - Company admin can perform all actions on their company's users
        - Company analyst can only read and update their own profile
        """
        if self.action == 'create':
            permission_classes = [IsSuperUser | IsAdminCompany]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrSuperUser]
        elif self.action == 'list':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'me':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsSuperUser]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        Set company based on the creating user (unless they're a superuser)
        """
        user = self.request.user
        
        # If a superuser is creating the user, use the company from the request
        if user.is_superuser:
            serializer.save()
        # If a company admin is creating a user, force the company to be their own
        elif user.is_admin_company:
            serializer.save(company=user.company)
    
    @action(detail=False, methods=['get'])
    @extend_schema(
        description="Get the current user's profile",
        responses={200: UserSerializer}
    )
    def me(self, request):
        """
        Get the current user's profile
        """
        serializer = self.get_serializer(request.user)
        return success_response(
            data=serializer.data,
            message="User profile retrieved successfully"
        ) 