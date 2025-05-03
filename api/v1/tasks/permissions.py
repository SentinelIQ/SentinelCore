from rest_framework import permissions
from api.core.rbac import HasEntityPermission


class TaskPermission(HasEntityPermission):
    """
    Permission class for Task model.
    
    Leverages the RBAC system to check permissions according to the role-permission matrix.
    Task entity type is automatically determined from the view's queryset.
    
    Permissions enforced by RBAC matrix:
    - Superuser has full access to all tasks
    - Company admin has full access to their company's tasks
    - Company analyst can create, view, and update tasks in their company
    - Read-only users can only view tasks in their company
    """ 