from rest_framework import permissions
from api.core.rbac import HasEntityPermission
from api.core.permissions import IsSuperUser, IsAdminCompany, IsAnalystCompany


class MISPPermission(HasEntityPermission):
    """
    Permission class for MISP resources.
    This class enforces RBAC based on entity type and role.
    
    - Server management and synchronization requires admin or superuser privileges
    - Events and attributes can be viewed by analysts and admins
    - Only company members can access their company's MISP data
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check for MISP resources.
        Enforces company-based isolation.
        """
        # First check basic permissions
        if not super().has_permission(request, view):
            return False
        
        # Superusers have full access
        if request.user.is_superuser:
            return True
        
        # Company isolation - users can only access objects from their company
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        elif hasattr(obj, 'event') and hasattr(obj.event, 'company'):
            return obj.event.company == request.user.company
        
        # Fail closed for safety
        return False

__all__ = ['MISPPermission']
