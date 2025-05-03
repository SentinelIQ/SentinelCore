from rest_framework import permissions
from api.core.rbac import HasEntityPermission


class AlertPermission(HasEntityPermission):
    """
    Permission class for Alert model.
    
    Leverages the RBAC system to check permissions according to the role-permission matrix.
    Alert entity type is automatically determined from the view's queryset.
    
    Permissions enforced by RBAC matrix:
    - Superuser has full access to all alerts
    - Company admin has full access to their company's alerts
    - Company analyst can create, view, and update alerts in their company
    - Read-only users can only view alerts in their company
    """ 