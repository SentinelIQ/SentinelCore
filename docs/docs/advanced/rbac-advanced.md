---
sidebar_position: 1
---

# Advanced RBAC

This guide provides an in-depth look at SentinelIQ's Role-Based Access Control (RBAC) system, covering advanced topics beyond the basics.

## Advanced Permission Matrix

SentinelIQ uses a comprehensive permission matrix that maps roles to permissions for different entity types. The advanced implementation includes:

- **Hierarchical Roles** - Roles can inherit permissions from other roles
- **Fine-grained Actions** - Permissions for specific actions beyond basic CRUD
- **Entity-specific Permissions** - Different permission sets for different entity types
- **Dynamic Permission Evaluation** - Permissions can be evaluated based on context

## Custom Permission Classes

Creating custom permission classes for specific business logic:

```python
from api.core.permissions import BasePermission

class IsOwnerOrTeamMember(BasePermission):
    """
    Allow access only to owners or team members.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Check if user is the owner
        if hasattr(obj, 'created_by') and obj.created_by == user:
            return True
            
        # Check if user is in the team
        if hasattr(obj, 'team') and user in obj.team.members.all():
            return True
            
        return False
```

## Permission Composition

Combining multiple permission classes:

```python
from api.core.rbac import HasEntityPermission
from api.core.permissions import IsAdminCompany
from rest_framework.permissions import OR

class ResourceViewSet(ViewSet):
    permission_classes = [OR(HasEntityPermission, IsAdminCompany)]
    entity_type = 'resource'
```

## Row-Level Security

Implementing row-level security with query filters:

```python
class ResourceViewSet(ViewSet):
    def get_queryset(self):
        base_queryset = super().get_queryset()
        
        user = self.request.user
        if user.is_superuser:
            return base_queryset
            
        # Filter by company
        queryset = base_queryset.filter(company=user.company)
        
        # Additional filters based on role
        if user.role == 'analyst':
            return queryset.filter(
                models.Q(assigned_to=user) | 
                models.Q(team__members=user)
            )
        
        return queryset
```

## Field-Level Permissions

Implementing field-level access control:

```python
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        request = self.context.get('request')
        if not request or not request.user:
            return
            
        user = request.user
        allowed_fields = self.get_allowed_fields(user)
        
        # Remove fields the user doesn't have permission to see
        existing = set(self.fields)
        for field_name in existing - allowed_fields:
            self.fields.pop(field_name)
    
    def get_allowed_fields(self, user):
        """Get fields the user has permission to access."""
        all_fields = set(self.fields)
        
        if user.is_superuser:
            return all_fields
            
        # Different fields for different roles
        if user.role == 'admin':
            return all_fields
        elif user.role == 'analyst':
            return all_fields - {'sensitive_data', 'internal_notes'}
        else:
            return all_fields - {'sensitive_data', 'internal_notes', 'technical_details'}
```

## Permission Auditing

Tracking permission checks for auditing:

```python
class AuditedPermission(BasePermission):
    def has_permission(self, request, view):
        result = self._check_permission(request, view)
        
        # Log the permission check
        log_permission_check(
            user=request.user,
            view=view.__class__.__name__,
            action=view.action,
            result=result
        )
        
        return result
    
    def _check_permission(self, request, view):
        """Implement actual permission logic here."""
        pass
```

## Best Practices for Advanced RBAC

1. **Caching** - Cache permission results to improve performance
2. **Explicit Denials** - Implement explicit denials (not just absence of permission)
3. **Separation of Concerns** - Keep permission logic separate from business logic
4. **Testing** - Thoroughly test permissions with all role combinations
5. **Documentation** - Document complex permission logic

## Performance Optimization

Optimizing permission checks for performance:

```python
from django.core.cache import cache

def get_user_permissions(user, entity_type):
    """Get user permissions with caching."""
    cache_key = f'user_permissions:{user.id}:{entity_type}'
    
    # Try to get from cache
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    # Compute permissions
    permissions = compute_user_permissions(user, entity_type)
    
    # Cache the result
    cache.set(cache_key, permissions, timeout=3600)  # 1 hour
    
    return permissions
```

## Advanced Role Management

Implementing role hierarchy and inheritance:

```python
ROLE_HIERARCHY = {
    'superuser': ['admin', 'analyst', 'viewer'],
    'admin': ['analyst', 'viewer'],
    'analyst': ['viewer'],
    'viewer': []
}

def user_has_role(user, required_role):
    """Check if user has the required role or higher."""
    user_role = get_user_role(user)
    
    # Direct match
    if user_role == required_role:
        return True
    
    # Check inheritance
    return required_role in ROLE_HIERARCHY.get(user_role, [])
```

By implementing these advanced RBAC patterns, you'll have a highly flexible and secure permission system capable of handling complex business requirements. 