from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from api.core.pagination import StandardResultsSetPagination
from api.core.viewsets import UpdateModelMixin, DestroyModelMixin
from ..serializers import UserSerializer
from ..filters import UserFilter
from ..permissions import UserPermission
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample

from .user_create import UserCreateMixin
from .user_detail import UserDetailMixin
from .user_custom_actions import UserCustomActionsMixin
from .token import CustomTokenObtainPairView, CustomTokenRefreshView, EmailPasswordTokenObtainView

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="List all users",
        description="Returns a list of all users the current user has permission to view, with pagination.",
        responses={
            200: OpenApiResponse(
                description="Success",
                examples=[
                    OpenApiExample(
                        name="user_list",
                        summary="User list example",
                        description="Example response with paginated user list",
                        value={
                            "status": "success",
                            "message": "Data retrieved successfully",
                            "data": [
                                {
                                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                    "username": "analyst1@example.com",
                                    "email": "analyst1@example.com",
                                    "first_name": "John",
                                    "last_name": "Doe",
                                    "role": "analyst",
                                    "is_active": True,
                                    "company": {
                                        "id": "4fa85f64-5717-4562-b3fc-2c963f66afb7",
                                        "name": "Example Corp"
                                    },
                                    "date_joined": "2023-01-15T10:00:00Z"
                                },
                                {
                                    "id": "5fa85f64-5717-4562-b3fc-2c963f66afc8",
                                    "username": "admin1@example.com",
                                    "email": "admin1@example.com",
                                    "first_name": "Jane",
                                    "last_name": "Smith",
                                    "role": "admin",
                                    "is_active": True,
                                    "company": {
                                        "id": "4fa85f64-5717-4562-b3fc-2c963f66afb7",
                                        "name": "Example Corp"
                                    },
                                    "date_joined": "2023-01-10T12:00:00Z"
                                }
                            ],
                            "metadata": {
                                "pagination": {
                                    "count": 2,
                                    "page": 1,
                                    "pages": 1,
                                    "page_size": 50,
                                    "next": None,
                                    "previous": None
                                }
                            }
                        }
                    )
                ]
            )
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve user details",
        description="Returns detailed information about a specific user.",
        responses={
            200: OpenApiResponse(
                description="Success",
                examples=[
                    OpenApiExample(
                        name="user_detail",
                        summary="User detail example",
                        description="Example response with detailed user information",
                        value={
                            "status": "success",
                            "message": "Data retrieved successfully",
                            "data": {
                                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "username": "analyst1@example.com",
                                "email": "analyst1@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "role": "analyst",
                                "is_active": True,
                                "is_superuser": False,
                                "is_admin_company": False,
                                "is_analyst_company": True,
                                "is_read_only": False,
                                "phone": "+1234567890",
                                "company": {
                                    "id": "4fa85f64-5717-4562-b3fc-2c963f66afb7",
                                    "name": "Example Corp"
                                },
                                "date_joined": "2023-01-15T10:00:00Z",
                                "last_login": "2023-05-20T14:30:00Z"
                            }
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description="User not found",
                examples=[
                    OpenApiExample(
                        name="user_not_found",
                        summary="User not found example",
                        description="Example response when the user doesn't exist or can't be accessed",
                        value={
                            "status": "error",
                            "message": "User not found",
                            "code": 404
                        }
                    )
                ]
            )
        }
    ),
    create=extend_schema(
        summary="Create a new user",
        description="Creates a new user account with the provided data.",
        responses={
            201: OpenApiResponse(
                description="User created successfully",
                examples=[
                    OpenApiExample(
                        name="user_created",
                        summary="User created example",
                        description="Example response when a user is created successfully",
                        value={
                            "status": "success",
                            "message": "User created successfully",
                            "data": {
                                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "username": "newuser@example.com",
                                "email": "newuser@example.com",
                                "first_name": "New",
                                "last_name": "User",
                                "role": "analyst",
                                "is_active": True,
                                "company": {
                                    "id": "4fa85f64-5717-4562-b3fc-2c963f66afb7",
                                    "name": "Example Corp"
                                },
                                "date_joined": "2023-06-15T10:00:00Z"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid request data",
                examples=[
                    OpenApiExample(
                        name="validation_error",
                        summary="Validation error example",
                        description="Example response when the request data is invalid",
                        value={
                            "status": "error",
                            "message": "Invalid request data",
                            "errors": {
                                "username": ["This field is required."],
                                "email": ["Enter a valid email address."],
                                "password": ["This password is too short. It must contain at least 8 characters."]
                            },
                            "code": 400
                        }
                    )
                ]
            )
        }
    ),
    update=extend_schema(
        summary="Update a user",
        description="Updates all fields of an existing user.",
        responses={
            200: OpenApiResponse(
                description="User updated successfully",
                examples=[
                    OpenApiExample(
                        name="user_updated",
                        summary="User updated example",
                        description="Example response when a user is updated successfully",
                        value={
                            "status": "success",
                            "message": "User updated successfully",
                            "data": {
                                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "username": "updateduser@example.com",
                                "email": "updateduser@example.com",
                                "first_name": "Updated",
                                "last_name": "User",
                                "role": "admin",
                                "is_active": True,
                                "company": {
                                    "id": "4fa85f64-5717-4562-b3fc-2c963f66afb7",
                                    "name": "Example Corp"
                                },
                                "date_joined": "2023-01-15T10:00:00Z"
                            }
                        }
                    )
                ]
            )
        }
    ),
    partial_update=extend_schema(
        summary="Partially update a user",
        description="Updates specific fields of an existing user.",
        responses={
            200: OpenApiResponse(
                description="User updated successfully",
                examples=[
                    OpenApiExample(
                        name="user_partially_updated",
                        summary="User partially updated example",
                        description="Example response when a user is partially updated successfully",
                        value={
                            "status": "success",
                            "message": "User updated successfully",
                            "data": {
                                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "username": "user@example.com",
                                "email": "user@example.com",
                                "first_name": "Updated",
                                "last_name": "Name",
                                "role": "analyst",
                                "is_active": True,
                                "company": {
                                    "id": "4fa85f64-5717-4562-b3fc-2c963f66afb7",
                                    "name": "Example Corp"
                                },
                                "date_joined": "2023-01-15T10:00:00Z"
                            }
                        }
                    )
                ]
            )
        }
    ),
    destroy=extend_schema(
        summary="Delete a user",
        description="Permanently deletes a user from the system.",
        responses={
            204: OpenApiResponse(
                description="User deleted successfully",
                examples=[
                    OpenApiExample(
                        name="user_deleted",
                        summary="User deleted example",
                        description="Example response when a user is deleted successfully",
                        value={
                            "status": "success",
                            "message": "User deleted successfully",
                            "data": None
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied example",
                        description="Example response when the user doesn't have permission to delete the user",
                        value={
                            "status": "error",
                            "message": "You do not have permission to delete this user",
                            "code": 403
                        }
                    )
                ]
            )
        }
    )
)
@extend_schema(tags=['Authentication & Access Control'])
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
    
    def get_queryset(self):
        """
        Returns users based on permission level:
        - Superusers see all users
        - Company admins see users in their company
        - Regular users see only themselves
        """
        # Handle schema generation
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return User.objects.none()
            
        user = self.request.user
        
        # Superuser sees all users
        if user.is_superuser:
            return User.objects.all()
            
        # Company admin sees users in their company
        if user.is_admin_company and hasattr(user, 'company') and user.company:
            return User.objects.filter(company=user.company)
            
        # Regular user sees only themselves
        return User.objects.filter(id=user.id)

__all__ = [
    'UserViewSet',
    'CustomTokenObtainPairView',
    'CustomTokenRefreshView',
    'EmailPasswordTokenObtainView',
]
