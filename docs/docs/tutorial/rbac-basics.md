---
sidebar_position: 5
---

# RBAC Basics

SentinelIQ implements a robust Role-Based Access Control (RBAC) system to secure all API endpoints. This guide introduces the basics of working with the RBAC system.

## Overview

Role-Based Access Control (RBAC) is a method of restricting system access to authorized users based on their roles within an organization. SentinelIQ's RBAC system provides:

- **Fine-grained Permission Control** - Control access at the entity and action level
- **Multi-tenant Isolation** - Secure data separation between companies/tenants
- **Role Hierarchy** - Structured role organization with inheritance

## Core RBAC Components

### Permission Matrix

The RBAC system uses a permission matrix defined in `auth_app.permission_matrix`:

```python
PERMISSION_MATRIX = {
    'alert': {
        'admin': ['create', 'read', 'update', 'delete', 'list', 'escalate'],
        'analyst': ['read', 'update', 'list', 'escalate'],
        'viewer': ['read', 'list'],
    },
    'incident': {
        'admin': ['create', 'read', 'update', 'delete', 'list', 'close'],
        'analyst': ['read', 'update', 'list'],
        'viewer': ['read', 'list'],
    },
    # Other entities...
}
```

This matrix maps roles to allowed actions for each entity type.

### Entity Permission Class

The `HasEntityPermission` class is the core of the RBAC system:

```python
from api.core.rbac import HasEntityPermission

class AlertViewSet(ViewSet):
    permission_classes = [HasEntityPermission]
    entity_type = 'alert'
```

By specifying the `entity_type`, the permission class will check if the user's role has permission to perform the requested action on that entity type.

## Using RBAC in Views

To implement RBAC in your views, follow these steps:

1. **Import the Permission Class**:
   ```python
   from api.core.rbac import HasEntityPermission
   ```

2. **Specify the Entity Type**:
   ```python
   class MyResourceViewSet(ViewSet):
       permission_classes = [HasEntityPermission]
       entity_type = 'my_resource'
   ```

3. **Define Actions**:
   Actions are automatically mapped from view methods:
   - `list` - GET request to the collection
   - `retrieve` - GET request to a specific resource
   - `create` - POST request to the collection
   - `update` - PUT request to a specific resource
   - `partial_update` - PATCH request to a specific resource
   - `destroy` - DELETE request to a specific resource

   Custom actions are also supported:
   ```python
   @action(detail=True, methods=['post'])
   def activate(self, request, pk=None):
       # This action will check for 'activate' permission
   ```

## Multi-tenant Isolation

The RBAC system automatically enforces tenant isolation:

```python
def has_object_permission(self, request, view, obj):
    # First check basic permission
    if not self.has_permission(request, view):
        return False
    
    # Then check tenant isolation - user can only access objects in their company
    return obj.company.id == request.user.company.id
```

This ensures that users can only access data belonging to their own company.

## Permission Classes

SentinelIQ provides several pre-defined permission classes:

- `HasEntityPermission` - Checks against the permission matrix
- `IsSuperUser` - Allows access only to superusers
- `IsAdminCompany` - Allows access only to company administrators
- `IsAnalystCompany` - Allows access only to company analysts
- `IsCompanyMember` - Allows access only to members of a company
- `IsOwnerOrSuperUser` - Allows access only to the owner of an object or superusers
- `ReadOnly` - Allows read-only access

## Testing RBAC

When testing your RBAC implementation, ensure you test:

1. Different roles trying to access the same resource
2. The same role accessing resources from different tenants
3. Custom actions with specific permissions

Example test:

```python
def test_analyst_cannot_delete_alert(self):
    self.client.force_authenticate(user=self.analyst_user)
    url = reverse('alert-detail', kwargs={'pk': self.alert.id})
    response = self.client.delete(url)
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

## Best Practices

1. **Always Use RBAC** - Every endpoint should be protected
2. **Granular Permissions** - Define specific permissions for different actions
3. **Principle of Least Privilege** - Grant the minimum permissions needed
4. **Test Thoroughly** - Test all role and permission combinations
5. **Audit Access** - Log all access attempts and permission denials

By following these principles, you'll ensure a secure API with proper access controls. 