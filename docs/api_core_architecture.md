# SentinelIQ API Core Architecture

## Overview

The `api.core` package provides a comprehensive set of utilities, mixins, and standardized components that ensure consistency, security, and enterprise-grade quality across the SentinelIQ platform API. This document outlines the architectural principles, key components, and implementation patterns that must be followed when developing new API endpoints.

## Key Components

### Response System (`api.core.responses`)

The response system ensures standardized formatting for all API responses:

```python
from api.core.responses import success_response, error_response, created_response, no_content_response

# Success response
return success_response(data=serializer.data, message="Operation completed successfully")

# Created response
return created_response(data=serializer.data, message="Resource created successfully")

# Error response
return error_response(message="Invalid input", errors=serializer.errors, status_code=400)

# No content response (for deletions)
return no_content_response()
```

All responses follow the structure:

```json
{
  "status": "success|error|warning",
  "data": { ... },
  "message": "Human-readable message",
  "metadata": { ... }
}
```

### Role-Based Access Control (`api.core.rbac`)

RBAC is the foundational security model:

```python
from api.core.rbac import HasEntityPermission

class YourModelViewSet(viewsets.ModelViewSet):
    permission_classes = [HasEntityPermission]
    entity_type = 'your_model'  # Must match permission matrix
```

The `HasEntityPermission` class checks permissions based on:
1. The user's role
2. The entity type (resource)
3. The action being performed
4. Tenant isolation (company-based)

### Enhanced ViewSets (`api.core.viewsets`)

Standard ViewSets with consistent response formatting:

```python
from api.core.viewsets import StandardViewSet, ReadOnlyViewSet

class YourModelViewSet(StandardViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
```

The `StandardViewSet` provides:
- Standardized response formatting
- Transaction-based operations
- Consistent error handling
- Customizable success messages

### Pagination (`api.core.pagination`)

Standardized pagination with metadata:

```python
from api.core.pagination import StandardResultsSetPagination, LargeResultsSetPagination

class YourModelViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
```

Available pagination classes:
- `StandardResultsSetPagination` (50 items)
- `LargeResultsSetPagination` (100 items)
- `SmallResultsSetPagination` (10 items)
- `CustomPageSizePagination` (dynamic size)

### Exception Handling (`api.core.exceptions`)

Centralized exception handling with standardized formats:

```python
# Automatically applied to all API views when configured in settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.core.exceptions.custom_exception_handler',
}
```

### Middleware (`api.core.middleware`)

Key middleware components:
- `RequestLoggingMiddleware`: Detailed API request/response logging
- `TenantContextMiddleware`: Company (tenant) context
- `SentryContextMiddleware`: Error tracking with enhanced context

### Audit System (`api.core.audit`)

Comprehensive audit logging:

```python
from api.core.audit import AuditLogMixin, audit_action

class YourModelViewSet(AuditLogMixin, StandardViewSet):
    entity_type = 'your_model'
    
    @audit_action(action_type='custom_action', entity_type='your_model')
    def custom_action(self, request, pk=None):
        # Custom action implementation
        return success_response(...)
```

The audit system provides:
- Automatic tracking of CRUD operations
- Custom action auditing via decorators
- Celery task auditing
- Integration with Sentry for security events

## Implementation Patterns

### 1. Modular View Structure

```
your_app/
├── views/
│   ├── __init__.py               # Imports all views and provides unified access
│   ├── resource_create.py        # Creation views
│   ├── resource_detail.py        # Detail & update views
│   └── resource_list.py          # List views
```

### 2. ViewSet Composition

```python
from api.core.viewsets import StandardViewSet
from api.core.rbac import HasEntityPermission
from api.core.audit import AuditLogMixin
from api.core.pagination import StandardResultsSetPagination

class YourModelViewSet(AuditLogMixin, StandardViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [HasEntityPermission]
    entity_type = 'your_model'
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Enforce tenant isolation
        return super().get_queryset().filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # Assign company automatically
        return serializer.save(company=self.request.user.company)
```

### 3. API Documentation

Use `drf-spectacular` annotations for all API endpoints:

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    tags=["Resource Category"],
    description="Detailed description of the endpoint",
    parameters=[
        OpenApiParameter(
            name="filter_param", 
            description="Parameter description",
            required=False, 
            type=str
        )
    ],
    responses={
        201: YourModelSerializer,
        400: "Error response structure"
    }
)
def create(self, request, *args, **kwargs):
    return super().create(request, *args, **kwargs)
```

### 4. URL Naming (kebab-case)

```python
router = DefaultRouter()
router.register(r'your-resources', YourModelViewSet)
router.register(r'your-resources/custom-endpoint', YourCustomViewSet)
```

## Testing Strategy

Follow the centralized testing approach:

```
tests/
├── your_app/
│   ├── test_your_model_create.py
│   ├── test_your_model_list.py
│   └── test_your_model_permissions.py
```

Key testing principles:
1. Test tenant isolation
2. Test permissions for different roles
3. Verify response formatting
4. Check audit log entries
5. Validate error handling

## Implementation Checklist

When implementing new API endpoints, ensure you:

- [ ] Create app using `docker compose exec web python manage.py startapp <app_name>`
- [ ] Follow modular view structure
- [ ] Extend core ViewSet classes
- [ ] Implement RBAC with `HasEntityPermission`
- [ ] Add audit logging with `AuditLogMixin`
- [ ] Register models for auditing in `api.core.audit_registration`
- [ ] Document all endpoints with `@extend_schema`
- [ ] Register models in Django Admin
- [ ] Create centralized tests
- [ ] Use kebab-case for URL paths
- [ ] Configure appropriate logging

## Best Practices

1. **Always enforce tenant isolation**:
   ```python
   def get_queryset(self):
       return super().get_queryset().filter(company=self.request.user.company)
   ```

2. **Use transactions for data integrity**:
   ```python
   from django.db import transaction
   
   @transaction.atomic
   def your_method(self, request, *args, **kwargs):
       # Implementation within transaction
   ```

3. **Log security-critical operations**:
   ```python
   from api.core.audit_sentry import security_critical
   
   @security_critical(event_name='critical_operation')
   def your_critical_method(self, request, *args, **kwargs):
       # Critical implementation
   ```

4. **Always use standardized responses**:
   ```python
   from api.core.responses import success_response
   
   return success_response(data=result, message="Operation successful")
   ```

5. **Implement proper serializer validation**:
   ```python
   def validate(self, data):
       # Custom validation logic
       if some_condition:
           raise serializers.ValidationError("Validation error message")
       return data
   ```

## Further Reading

- [RBAC System](./rbac_system.md)
- [Sentry Integration](./sentry-integration.md)
- [Compliance Requirements](./compliance.md)
- [Celery Configuration](./celery-config.md)
- [API Tag Structure](./api_tag_structure.md) 