from rest_framework import permissions
from api.core.rbac import HasEntityPermission


class UserPermission(HasEntityPermission):
    """
    Permission class for User model.
    
    Leverages the RBAC system to check permissions according to the role-permission matrix.
    User entity type is automatically determined from the view's queryset.
    
    Permissions enforced by RBAC matrix:
    - Superuser can do everything
    - Company admin can manage users in their company
    - Users can view and update their own profile
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the specific user object.
        
        Extends the standard tenant isolation with special rule for own profile:
        - Users can always view/edit their own profile regardless of role
        
        Args:
            request: The request object
            view: The view object
            obj: The User object being accessed
            
        Returns:
            bool: True if the user has permission, False otherwise
        """
        # Users can always access their own profile
        if obj.id == request.user.id:
            return True
            
        # Use the standard RBAC object permission check for other cases
        return super().has_object_permission(request, view, obj) 