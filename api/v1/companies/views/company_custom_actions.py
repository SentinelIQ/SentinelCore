from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from api.core.responses import success_response, error_response
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class CompanyCustomActionsMixin:
    """
    Mixin for company custom actions.
    """
    
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