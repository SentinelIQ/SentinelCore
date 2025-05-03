"""
Permissions for common API endpoints.
"""
from rest_framework import permissions
from api.core.rbac import HasEntityPermission
from django.contrib.auth import get_user_model

User = get_user_model()


class CommonPermission(HasEntityPermission):
    """
    Permission class for common API endpoints.
    
    Leverages the RBAC system to check permissions according to the role-permission matrix,
    with special handling for public endpoints like health check.
    """
    
    def has_permission(self, request, view):
        """
        Check permissions for common API views.
        
        Args:
            request: The request object
            view: The view object
            
        Returns:
            bool: True if the user has permission, False otherwise
        """
        # Health check is always accessible to anyone
        if view.action == 'health_check':
            return True
            
        # Whoami requires authentication but no specific permissions beyond that
        if view.action == 'whoami':
            return request.user and request.user.is_authenticated
            
        # For other actions, use the standard RBAC permission check
        return super().has_permission(request, view) 