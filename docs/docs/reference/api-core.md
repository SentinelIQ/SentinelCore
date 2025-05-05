---
sidebar_position: 1
---

# API Core Reference

The `api.core` module is the foundation of SentinelIQ, providing standardized components used across the entire platform. This reference documents the key classes and functions in the module.

## Responses (`api.core.responses`)

The responses module provides standardized response formatting.

### Functions

#### `success_response(data=None, message=None, meta=None, status_code=200)`

Returns a standardized success response.

**Parameters:**
- `data` (any, optional): The response data. Default: `None`
- `message` (str, optional): A human-readable message. Default: `None`
- `meta` (dict, optional): Additional metadata. Default: `None`
- `status_code` (int, optional): HTTP status code. Default: `200`

**Returns:**
- `Response`: A DRF Response object with standardized format

**Example:**
```python
from api.core.responses import success_response

def get_resource(request, id):
    resource = get_object_or_404(Resource, id=id)
    serializer = ResourceSerializer(resource)
    return success_response(
        data=serializer.data,
        message="Resource retrieved successfully"
    )
```

#### `created_response(data=None, message=None, meta=None)`

Returns a standardized 201 Created response.

**Parameters:**
- `data` (any, optional): The response data. Default: `None`
- `message` (str, optional): A human-readable message. Default: `None`
- `meta` (dict, optional): Additional metadata. Default: `None`

**Returns:**
- `Response`: A DRF Response object with status 201

#### `error_response(message, details=None, meta=None, status_code=400)`

Returns a standardized error response.

**Parameters:**
- `message` (str): A human-readable error message
- `details` (dict, optional): Detailed error information. Default: `None`
- `meta` (dict, optional): Additional metadata. Default: `None`
- `status_code` (int, optional): HTTP status code. Default: `400`

**Returns:**
- `Response`: A DRF Response object with error format

#### `no_content_response(message=None)`

Returns a standardized 204 No Content response.

**Parameters:**
- `message` (str, optional): A human-readable message. Default: `None`

**Returns:**
- `Response`: A DRF Response object with status 204

## RBAC (`api.core.rbac`)

The RBAC module implements role-based access control.

### Classes

#### `HasEntityPermission`

Permission class that checks if a user has permission to perform an action on an entity.

**Class Attributes:**
- None

**Instance Attributes:**
- `entity_type` (str): The type of entity to check permissions for

**Methods:**

##### `has_permission(request, view)`

Checks if the user has permission to access the view.

**Parameters:**
- `request` (Request): The request object
- `view` (View): The view being accessed

**Returns:**
- `bool`: True if the user has permission, False otherwise

##### `has_object_permission(request, view, obj)`

Checks if the user has permission to access the specific object.

**Parameters:**
- `request` (Request): The request object
- `view` (View): The view being accessed
- `obj` (Model): The object being accessed

**Returns:**
- `bool`: True if the user has permission, False otherwise

**Example:**
```python
from api.core.rbac import HasEntityPermission

class AlertViewSet(ViewSet):
    permission_classes = [HasEntityPermission]
    entity_type = 'alert'
```

## Permissions (`api.core.permissions`)

The permissions module provides reusable permission classes.

### Classes

#### `IsSuperUser`

Permission class that allows access only to superusers.

#### `IsAdminCompany`

Permission class that allows access only to company administrators.

#### `IsAnalystCompany`

Permission class that allows access only to company analysts.

#### `IsCompanyMember`

Permission class that allows access only to members of a company.

#### `IsOwnerOrSuperUser`

Permission class that allows access only to the owner of an object or superusers.

#### `ReadOnly`

Permission class that allows read-only access.

## Exception Handling (`api.core.exceptions`)

The exceptions module provides standardized error handling.

### Functions

#### `custom_exception_handler(exc, context)`

Custom exception handler that returns errors in a standard format.

**Parameters:**
- `exc` (Exception): The exception that was raised
- `context` (dict): Additional context information

**Returns:**
- `Response`: A standardized error response

## Pagination (`api.core.pagination`)

The pagination module provides standardized pagination classes.

### Classes

#### `StandardResultsSetPagination`

Standard pagination class (50 items per page).

**Attributes:**
- `page_size` (int): 50
- `page_size_query_param` (str): 'page_size'
- `max_page_size` (int): 100

#### `LargeResultsSetPagination`

Pagination class for large result sets (100 items per page).

**Attributes:**
- `page_size` (int): 100
- `page_size_query_param` (str): 'page_size'
- `max_page_size` (int): 200

#### `SmallResultsSetPagination`

Pagination class for small result sets (10 items per page).

**Attributes:**
- `page_size` (int): 10
- `page_size_query_param` (str): 'page_size'
- `max_page_size` (int): 50

#### `CustomPageSizePagination`

Pagination class with configurable page size.

**Attributes:**
- `page_size_query_param` (str): 'page_size'
- `max_page_size` (int): 1000

## Filtering (`api.core.filters`)

The filters module provides utilities for query parameter filtering.

### Classes

#### `ArrayFieldFilter`

Filter class for handling array field filtering.

**Parameters:**
- `field_name` (str): The name of the field to filter on

**Example:**
```python
from api.core.filters import ArrayFieldFilter

class AlertFilter(FilterSet):
    severity = ArrayFieldFilter(field_name='severity')
    status = ArrayFieldFilter(field_name='status')
    
    class Meta:
        model = Alert
        fields = ['severity', 'status', 'created_by', 'assigned_to']
```

### Functions

#### `get_array_field_filter_overrides()`

Gets the filter override configuration for array fields.

**Returns:**
- `dict`: Filter override configuration

## ViewSets (`api.core.viewsets`)

The viewsets module provides enhanced viewsets.

### Classes

#### `StandardViewSet`

Standard viewset that includes complete CRUD operations.

**Example:**
```python
from api.core.viewsets import StandardViewSet

class ResourceViewSet(StandardViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
```

#### `ReadOnlyViewSet`

Read-only viewset that includes only list and retrieve operations.

## Audit (`api.core.audit`)

The audit module provides integration with the audit logging system.

### Classes

#### `AuditLogMixin`

Mixin that adds audit logging functionality to a viewset.

**Attributes:**
- `audit_entity_type` (str): The type of entity being audited

**Methods:**

##### `log_action(action, obj, **kwargs)`

Logs an action on an object.

**Parameters:**
- `action` (str): The action being performed (e.g., 'create', 'update')
- `obj` (Model): The object being acted upon
- `**kwargs`: Additional data to include in the log

**Example:**
```python
from api.core.audit import AuditLogMixin

class ResourceViewSet(AuditLogMixin, ViewSet):
    audit_entity_type = 'resource'
    
    def create(self, request, *args, **kwargs):
        # ... create logic ...
        self.log_action('create', resource)
        # ...
```

## Middleware (`api.core.middleware`)

The middleware module includes middleware components.

### Classes

#### `RequestLoggingMiddleware`

Middleware that logs API requests.

#### `TenantContextMiddleware`

Middleware that sets tenant context based on request.

#### `SentryContextMiddleware`

Middleware that adds context for Sentry error tracking.

## Best Practices

When using the `api.core` module, follow these best practices:

1. **Always use response helpers** - Use the response helpers from `api.core.responses` for all API responses
2. **Use RBAC** - Use the RBAC system for all permission checks
3. **Standardize pagination** - Use the standard pagination classes
4. **Log audit events** - Use the audit logging system for all significant actions
5. **Handle exceptions consistently** - Use the exception handling system
6. **Document with OpenAPI** - Use the OpenAPI utilities to document endpoints 