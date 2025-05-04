"""
Role-Based Access Control (RBAC) for SentinelIQ.

This module implements the RBAC system for SentinelIQ.
"""

from rest_framework import permissions
from auth_app.permission_matrix import has_permission, get_required_permission
import logging

logger = logging.getLogger(__name__)


class HasEntityPermission(permissions.BasePermission):
    """
    Permission class that enforces entity-level permissions based on the RBAC matrix.
    
    This class checks if the user has the required permission for the entity
    based on their role and the permission matrix.
    """
    
    def has_permission(self, request, view):
        """
        Check if the user has permission to access the view.
        
        Args:
            request: The request object
            view: The view object
            
        Returns:
            bool: True if the user has permission, False otherwise
        """
        # Unauthenticated users have no permissions
        if not request.user.is_authenticated:
            return False
            
        # Determine entity_type from the view
        entity_type = getattr(view, 'entity_type', None)
        
        # If no entity_type is specified, try to determine from model name
        if not entity_type and hasattr(view, 'queryset'):
            entity_type = view.queryset.model.__name__.lower()
        elif not entity_type and hasattr(view, 'get_queryset'):
            try:
                entity_type = view.get_queryset().model.__name__.lower()
            except Exception:
                pass
                
        if not entity_type:
            # Default to the most restrictive permission check if entity_type cannot be determined
            logger.warning(f"Entity type could not be determined for view {view.__class__.__name__}")
            # Only superuser can access views with unknown entity types
            return request.user.is_superuser
            
        # Check for custom action
        custom_action = None
        # Handle both ViewSets (with action) and APIViews (without action)
        action = getattr(view, 'action', None)
        if action is not None and action not in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            custom_action = action
            
        # Get the required permission for this action
        required_permission = get_required_permission(
            request.method, 
            entity_type,
            custom_action
        )
        
        # Check if the user has the required permission
        has_perm = has_permission(request.user.role, required_permission)
        
        # Log debug info for permission checks
        logger.debug(
            f"RBAC: User {request.user.username} with role {request.user.role} "
            f"requesting {request.method} on {entity_type} "
            f"(action: {getattr(view, 'action', request.method.lower())}). Required permission: {required_permission}. "
            f"Result: {'GRANTED' if has_perm else 'DENIED'}"
        )
        
        return has_perm
        
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the object.
        
        This implements tenant isolation - users can only access objects 
        that belong to their company.
        
        Args:
            request: The request object
            view: The view object
            obj: The object being accessed
            
        Returns:
            bool: True if the user has permission, False otherwise
        """
        # Superusers can access everything
        if request.user.is_superuser:
            return True
            
        # First verify basic permission
        if not self.has_permission(request, view):
            return False
            
        # Tenant isolation check - users can only access objects in their company
        if hasattr(obj, 'company'):
            # Direct company attribute
            return obj.company == request.user.company
        elif hasattr(obj, 'get_company'):
            # Method to get company
            return obj.get_company() == request.user.company
        elif hasattr(obj, 'user') and hasattr(obj.user, 'company'):
            # Object belongs to a user who belongs to a company
            return obj.user.company == request.user.company
            
        # If the object itself is a company
        if obj.__class__.__name__.lower() == 'company':
            return obj == request.user.company
            
        # Default to deny if we can't determine company ownership
        logger.warning(
            f"Object permission check failed for {obj.__class__.__name__} - "
            f"cannot determine company ownership"
        )
        return False 