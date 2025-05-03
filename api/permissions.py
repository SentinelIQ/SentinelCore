from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Allows access only to superusers.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsAdminCompany(permissions.BasePermission):
    """
    Allows access only to company admins.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_admin_company)


class IsAnalystCompany(permissions.BasePermission):
    """
    Allows access only to company analysts.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_analyst_company)


class IsOwnerOrSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow owners of a company or superusers to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Allow superusers unrestricted access
        if request.user.is_superuser:
            return True
        
        # Allow admin company users access to their own company
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        elif hasattr(obj, 'users'):
            # If the object is a company
            return request.user in obj.users.all()
        
        # For user objects
        return obj == request.user


class ReadOnly(permissions.BasePermission):
    """
    Allows read-only access.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS 