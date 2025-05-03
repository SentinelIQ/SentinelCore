from rest_framework import permissions
from api.core.rbac import HasEntityPermission


class ObservablePermission(HasEntityPermission):
    """
    Permission class for Observable model.
    
    Leverages the RBAC system to check permissions according to the role-permission matrix.
    Observable entity type is automatically determined from the view's queryset.
    
    Permissions enforced by RBAC matrix:
    - Superuser has full access to all observables
    - Company admin has full access to their company's observables
    - Company analyst can create, view, and update observables in their company
    - Read-only users can only view observables in their company
    """ 