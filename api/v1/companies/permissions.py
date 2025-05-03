from rest_framework import permissions
from api.core.rbac import HasEntityPermission


class CompanyPermission(HasEntityPermission):
    """
    Permission class for Company model.
    
    Leverages the RBAC system to check permissions according to the role-permission matrix.
    Company entity type is automatically determined from the view's queryset.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the specific company object.
        
        Enforces company-level isolation: regular users can only access their own company.
        
        Args:
            request: The request object
            view: The view object
            obj: The Company object being accessed
            
        Returns:
            bool: True if the user has permission, False otherwise
        """
        # Use the parent class's tenant isolation logic
        return super().has_object_permission(request, view, obj) 