from rest_framework import permissions
from api.core.rbac import HasEntityPermission


class IncidentPermission(HasEntityPermission):
    """
    Permission class for Incident model.
    
    Leverages the RBAC system to check permissions according to the role-permission matrix.
    Incident entity type is automatically determined from the view's queryset.
    
    Permissions enforced by RBAC matrix:
    - Superuser has full access to all incidents
    - Company admin has full access to their company's incidents
    - Company analyst can create, view, and update incidents in their company
    - Read-only users can only view incidents in their company
    """ 