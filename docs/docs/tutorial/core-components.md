---
sidebar_position: 3
---

# Core Components

SentinelIQ's core components provide consistent, reusable functionality across the entire platform. These components are housed in the `api.core` module.

## Overview of Core Components

The `api.core` module includes:

1. **Response Handling** - Standardized API responses
2. **RBAC** - Role-based access control system
3. **Permissions** - Permission classes for various access levels
4. **Exception Handling** - Consistent error responses
5. **Pagination** - Result set pagination with standardized formats
6. **Filtering** - Query parameter filtering utilities
7. **Middleware** - Request/response processing
8. **Audit** - Centralized audit logging components
9. **Utilities** - Common utility functions
10. **OpenAPI** - Documentation enhancements

## Response Handling

The `api.core.responses` module provides standardized response formatting to ensure consistency across all API endpoints:

```python
from api.core.responses import (
    success_response,
    error_response,
    created_response,
    no_content_response
)

# Success response (200 OK)
def get_resource(request, id):
    resource = get_object_or_404(Resource, id=id)
    serializer = ResourceSerializer(resource)
    return success_response(
        data=serializer.data,
        message="Resource retrieved successfully"
    )

# Created response (201 Created)
def create_resource(request):
    serializer = ResourceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    resource = serializer.save()
    return created_response(
        data=serializer.data,
        message="Resource created successfully"
    )

# No content response (204 No Content)
def delete_resource(request, id):
    resource = get_object_or_404(Resource, id=id)
    resource.delete()
    return no_content_response(
        message="Resource deleted successfully"
    )

# Error response (400, 403, 404, 500)
def custom_error(request):
    return error_response(
        message="An error occurred",
        details={"field": "Error details"},
        status_code=400
    )
```

### Response Format

All responses follow a consistent format:

```json
{
  "status": "success",  // or "error"
  "data": {},           // Response data (if applicable)
  "message": "Human-readable message",
  "meta": {             // Additional metadata
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_pages": 5,
      "total_records": 42
    }
  }
}
```

## RBAC (Role-Based Access Control)

The `api.core.rbac` module implements a comprehensive role-based access control system:

```python
from api.core.rbac import HasEntityPermission

class AlertViewSet(ViewSet):
    permission_classes = [HasEntityPermission]
    entity_type = 'alert'  # Corresponds to permission matrix
```

### Permission Matrix

The RBAC system uses a permission matrix defined in the authentication app:

```python
# auth_app/permission_matrix.py
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

## Permission Classes

The `api.core.permissions` module includes reusable permission classes:

```python
from api.core.permissions import (
    IsSuperUser,
    IsAdminCompany,
    IsAnalystCompany,
    IsCompanyMember,
    IsOwnerOrSuperUser,
    ReadOnly
)

class ResourceViewSet(ViewSet):
    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminCompany()]
        elif self.action in ['list', 'retrieve']:
            return [IsCompanyMember()]
        return [IsSuperUser()]
```

## Exception Handling

The `api.core.exceptions` module provides consistent error handling:

```python
# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.core.exceptions.custom_exception_handler',
    # ...
}

# api.core.exceptions.py
def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns errors in a standard format.
    """
    # Default handler
    response = exception_handler(exc, context)
    
    if response is not None:
        # Transform error to standard format
        response.data = {
            'status': 'error',
            'message': get_error_message(exc),
            'details': get_error_details(exc),
            'code': response.status_code
        }
    
    # Log the error
    log_error(exc, context)
    
    return response
```

## Pagination

The `api.core.pagination` module includes standardized pagination classes:

```python
from api.core.pagination import StandardResultsSetPagination

class ResourceViewSet(ViewSet):
    pagination_class = StandardResultsSetPagination
```

Pagination classes include:

- `StandardResultsSetPagination` (50 items per page)
- `LargeResultsSetPagination` (100 items)
- `SmallResultsSetPagination` (10 items)
- `CustomPageSizePagination` (configurable)

## Filtering

The `api.core.filters` module provides utilities for query parameter filtering:

```python
from api.core.filters import ArrayFieldFilter

class AlertFilter(FilterSet):
    severity = ArrayFieldFilter(field_name='severity')
    status = ArrayFieldFilter(field_name='status')
    
    class Meta:
        model = Alert
        fields = ['severity', 'status', 'created_by', 'assigned_to']

class AlertViewSet(ViewSet):
    filterset_class = AlertFilter
```

## Middleware

The `api.core.middleware` module includes middleware components for:

- `RequestLoggingMiddleware` - Logs API requests
- `TenantContextMiddleware` - Sets tenant context based on request
- `SentryContextMiddleware` - Adds context for Sentry error tracking

## ViewSets

The `api.core.viewsets` module provides enhanced viewsets:

```python
from api.core.viewsets import StandardViewSet

class ResourceViewSet(StandardViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    # Additional configuration...
```

Available viewsets include:

- `StandardViewSet` - Complete CRUD operations
- `ReadOnlyViewSet` - List and retrieve operations only

## Audit Integration

The `api.core.audit` module provides integration with the audit logging system:

```python
from api.core.audit import AuditLogMixin

class ResourceViewSet(AuditLogMixin, ViewSet):
    audit_entity_type = 'resource'
    
    def create(self, request, *args, **kwargs):
        # ...
        # Log the action
        self.log_action('create', resource)
        # ...
```

## Using Core Components

When building new features, always leverage these core components to ensure consistency:

1. Use response helpers from `api.core.responses` for all API responses
2. Use RBAC and permission classes for access control
3. Use standard pagination classes
4. Use filter utilities for query parameter handling
5. Integrate with the audit logging system
6. Use standard viewsets where possible

## Best Practices

When working with core components:

1. **Don't Duplicate** - If functionality exists in core, use it instead of reimplementing
2. **Extend Don't Modify** - Extend core components for specific needs rather than modifying them
3. **Consistent Usage** - Use core components consistently across all modules
4. **Documentation** - Document custom extensions or usages

In the next section, we'll look more closely at [response handling](response-handling) in SentinelIQ. 