from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Allows access only to superusers.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsAdminCompany(permissions.BasePermission):
    """
    Allows access only to company administrators.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_admin_company)


class IsAnalystCompany(permissions.BasePermission):
    """
    Allows access only to company analysts.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_analyst_company)


class IsCompanyMember(permissions.BasePermission):
    """
    Verifies if the user belongs to the object's company.
    """
    def has_object_permission(self, request, view, obj):
        # Superuser has access to everything
        if request.user.is_superuser:
            return True
        
        # For objects with company reference
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        
        # For objects that are companies
        elif hasattr(obj, 'users'):
            return request.user in obj.users.all()
        
        # Default case for user objects
        elif hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        return False


class IsOwnerOrSuperUser(permissions.BasePermission):
    """
    Allows access only to the owner of an object or a superuser.
    
    The object must have a user, owner, or created_by field that points to a user,
    or the object must be a user object itself.
    """
    def has_object_permission(self, request, view, obj):
        # Superuser can do anything
        if request.user.is_superuser:
            return True
            
        # Check if object is a user
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            if obj.id == request.user.id:
                return True
                
        # Check common owner field names
        for field in ['user', 'owner', 'created_by', 'author']:
            if hasattr(obj, field):
                owner = getattr(obj, field)
                if owner == request.user:
                    return True
                    
        return False


class ReadOnly(permissions.BasePermission):
    """
    Allows only read operations (GET, HEAD, OPTIONS).
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS 