from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from api.core.responses import success_response, error_response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class CompanyCustomActionsMixin:
    """
    Mixin for company custom actions.
    """
    
    @extend_schema(
        summary="List company users",
        description=(
            "Retrieves all users belonging to the specified company. This endpoint is crucial for "
            "tenant management in the multi-tenant SOAR platform. It provides visibility into "
            "user accounts within an organization, allowing administrators to manage access "
            "and permissions. The list includes user details such as username, email, role, "
            "and active status. This information is used for user administration, audit, "
            "and governance purposes within the security operations team."
        ),
        responses={
            200: OpenApiResponse(
                description="Users retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="company_users",
                        summary="Company users list",
                        description="Example showing a list of company users",
                        value={
                            "status": "success",
                            "message": "Users retrieved for company: Acme Corporation",
                            "data": [
                                {
                                    "id": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                                    "username": "john.smith",
                                    "email": "john.smith@acme.com",
                                    "first_name": "John",
                                    "last_name": "Smith",
                                    "role": "admin_company",
                                    "is_active": True,
                                    "last_login": "2023-07-10T14:32:10.123456Z"
                                },
                                {
                                    "id": "b2840a9b-8ecb-558a-0f7d-1c46e2f9cd31",
                                    "username": "jane.doe",
                                    "email": "jane.doe@acme.com",
                                    "first_name": "Jane",
                                    "last_name": "Doe",
                                    "role": "analyst_company",
                                    "is_active": True,
                                    "last_login": "2023-07-12T09:45:22.789012Z"
                                }
                            ]
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied error",
                        description="Example of response when user lacks permission to view company users",
                        value={
                            "status": "error",
                            "message": "You do not have permission to view users for this company",
                            "data": None
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def users(self, request, pk=None):
        """
        Get all users for a specific company.
        
        Args:
            request: The HTTP request
            pk: The company primary key
            
        Returns:
            List of users belonging to the company
        """
        company = self.get_object()
        
        # RBAC will handle permission checks automatically through has_object_permission
        
        # Get users for this company
        users = User.objects.filter(company=company)
        
        # Use appropriate serializer
        from api.v1.auth.serializers import UserSerializer
        serializer = UserSerializer(users, many=True)
        
        return success_response(
            data=serializer.data,
            message=f"Users retrieved for company: {company.name}"
        )

    @extend_schema(
        summary="Get company statistics",
        description=(
            "Retrieves comprehensive statistics about a company's security operations. This endpoint "
            "provides key metrics including user counts, alert statistics, and incident data. "
            "Security leaders use this information to assess the operational status of their "
            "security program, understand alert volume and resolution rates, and monitor incident "
            "response effectiveness. The statistics are essential for capacity planning, resource "
            "allocation, and performance measurement in security operations centers (SOCs). "
            "Multi-tenant isolation ensures that each company only sees their own statistics."
        ),
        responses={
            200: OpenApiResponse(
                description="Statistics retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="company_statistics",
                        summary="Company statistics",
                        description="Example showing statistics for a company",
                        value={
                            "status": "success",
                            "message": "Statistics retrieved for company: Acme Corporation",
                            "data": {
                                "users": {
                                    "total": 25,
                                    "active": 22
                                },
                                "alerts": {
                                    "total": 1489,
                                    "open": 142,
                                    "closed": 1347
                                },
                                "incidents": {
                                    "total": 87,
                                    "open": 12,
                                    "closed": 75
                                }
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied error",
                        description="Example of response when user lacks permission to view company statistics",
                        value={
                            "status": "error",
                            "message": "You do not have permission to view statistics for this company",
                            "data": None
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def statistics(self, request, pk=None):
        """
        Get statistics for a specific company.
        
        Args:
            request: The HTTP request
            pk: The company primary key
            
        Returns:
            Statistics about the company (users, alerts, incidents)
        """
        company = self.get_object()
        
        # RBAC will handle permission checks automatically through has_object_permission
        
        # Collect statistics
        stats = {
            'users': {
                'total': User.objects.filter(company=company).count(),
                'active': User.objects.filter(company=company, is_active=True).count()
            }
        }
        
        # Add more statistics as needed (alerts, incidents, etc.)
        try:
            from alerts.models import Alert
            stats['alerts'] = {
                'total': Alert.objects.filter(company=company).count(),
                'open': Alert.objects.filter(company=company, status='open').count(),
                'closed': Alert.objects.filter(company=company, status='closed').count()
            }
        except ImportError:
            # Alerts module might not be available
            pass
            
        try:
            from incidents.models import Incident
            stats['incidents'] = {
                'total': Incident.objects.filter(company=company).count(),
                'open': Incident.objects.filter(company=company, status='open').count(),
                'closed': Incident.objects.filter(company=company, status='closed').count()
            }
        except ImportError:
            # Incidents module might not be available
            pass
        
        return success_response(
            data=stats,
            message=f"Statistics retrieved for company: {company.name}"
        )

    @extend_schema(
        summary="Get detailed user statistics",
        description=(
            "Retrieves detailed user statistics for a company, including breakdowns by role and "
            "status. This endpoint provides a more in-depth view of the user base than the basic "
            "statistics endpoint. Security administrators use this information to monitor team "
            "composition, track analyst-to-admin ratios, and manage user accounts. This information "
            "supports team planning, access management, and security governance processes. "
            "Access is restricted to company administrators and platform superusers to protect "
            "sensitive organizational information."
        ),
        responses={
            200: OpenApiResponse(
                description="User statistics retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="user_statistics",
                        summary="User statistics",
                        description="Example showing detailed user statistics for a company",
                        value={
                            "status": "success",
                            "message": "User statistics retrieved for company: Acme Corporation",
                            "data": {
                                "company": {
                                    "id": "7c637454-d1e9-4763-9aa8-c1050e07ad10",
                                    "name": "Acme Corporation"
                                },
                                "stats": {
                                    "total": 25,
                                    "active": 22,
                                    "inactive": 3,
                                    "admin_company": 4,
                                    "analyst_company": 21
                                }
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied error",
                        description="Example of response when user lacks permission to view user statistics",
                        value={
                            "status": "error",
                            "message": "You do not have permission to view user statistics for this company",
                            "code": "permission_denied"
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['get'], url_path='user-stats')
    def user_stats(self, request, pk=None):
        """
        Get user statistics for a specific company.
        
        Args:
            request: The HTTP request
            pk: The company primary key
            
        Returns:
            User statistics for the company
        """
        company = self.get_object()
        
        # RBAC handles base permission checks, but we need additional role-specific check
        # Only superuser and admin_company should access this action
        if not (request.user.is_superuser or request.user.role == User.Role.ADMIN_COMPANY):
            return error_response(
                message="You do not have permission to view user statistics for this company",
                code="permission_denied",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        users = company.users.all()
        
        stats = {
            'total': users.count(),
            'active': users.filter(is_active=True).count(),
            'inactive': users.filter(is_active=False).count(),
            'admin_company': users.filter(role=User.Role.ADMIN_COMPANY).count(),
            'analyst_company': users.filter(role=User.Role.ANALYST_COMPANY).count(),
        }
        
        return success_response(
            data={
                "company": {
                    "id": company.id,
                    "name": company.name
                },
                "stats": stats
            },
            message=f"User statistics retrieved for company: {company.name}"
        )
    
    @extend_schema(
        summary="Deactivate multiple users",
        description=(
            "Deactivates multiple user accounts within a company simultaneously. This endpoint "
            "is critical for security operations when off-boarding multiple employees or when "
            "responding to potential account compromises. Company administrators and platform "
            "superusers can use this feature to quickly revoke access for multiple users. "
            "The operation preserves user data for audit purposes while preventing further "
            "system access. Safety measures prevent company administrators from deactivating "
            "other administrators, which requires superuser privileges."
        ),
        request={
            "type": "object",
            "properties": {
                "user_ids": {
                    "type": "array",
                    "items": {"type": "string", "format": "uuid"},
                    "description": "List of user IDs to deactivate"
                }
            },
            "required": ["user_ids"]
        },
        responses={
            200: OpenApiResponse(
                description="Users deactivated successfully",
                examples=[
                    OpenApiExample(
                        name="deactivation_success",
                        summary="Users deactivated",
                        description="Example showing successful deactivation of users",
                        value={
                            "status": "success",
                            "message": "3 users were successfully deactivated",
                            "data": {
                                "deactivated_count": 3,
                                "requested_count": 4
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid request",
                examples=[
                    OpenApiExample(
                        name="empty_user_ids",
                        summary="No user IDs provided",
                        description="Example of response when no user IDs are provided",
                        value={
                            "status": "error",
                            "message": "You must provide at least one user ID",
                            "code": "invalid_request"
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied error",
                        description="Example of response when user lacks permission to deactivate users",
                        value={
                            "status": "error",
                            "message": "You do not have permission to deactivate users in this company",
                            "code": "permission_denied"
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['post'], url_path='deactivate-users')
    def deactivate_users(self, request, pk=None):
        """
        Deactivate multiple users in a company.
        
        Args:
            request: The HTTP request with user_ids list
            pk: The company primary key
            
        Returns:
            Count of deactivated users
        """
        company = self.get_object()
        
        # RBAC handles base permission checks, but we need additional role-specific check
        # Only superuser and admin_company should access this action
        if not (request.user.is_superuser or request.user.role == User.Role.ADMIN_COMPANY):
            return error_response(
                message="You do not have permission to deactivate users in this company",
                code="permission_denied",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return error_response(
                message="You must provide at least one user ID",
                code="invalid_request",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter users by company
        users = User.objects.filter(id__in=user_ids, company=company)
        
        # Don't allow deactivating other admins if the user is a company admin
        if not request.user.is_superuser:
            users = users.exclude(role=User.Role.ADMIN_COMPANY)
        
        count = users.update(is_active=False)
        
        logger.info(f"{count} users deactivated in company {company.name} by {request.user.username}")
        
        return success_response(
            data={
                "deactivated_count": count,
                "requested_count": len(user_ids)
            },
            message=f"{count} users were successfully deactivated"
        ) 