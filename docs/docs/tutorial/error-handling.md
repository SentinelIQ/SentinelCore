---
sidebar_position: 6
---

# Error Handling

SentinelIQ implements a standardized error handling mechanism across the platform. This guide explains how to use and extend the error handling system.

## Standardized Error Response Format

All error responses in SentinelIQ follow a consistent format:

```json
{
  "status": "error",
  "message": "An error occurred while processing your request",
  "details": {
    "field_name": ["Error details"]
  },
  "code": 400
}
```

This format ensures consistency across all endpoints and makes it easier for clients to handle errors.

## Custom Exception Handler

SentinelIQ uses a custom exception handler defined in `api.core.exceptions`:

```python
# api.core.exceptions.py
def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns errors in a standard format.
    """
    response = exception_handler(exc, context)
    
    if response is not None:
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

This handler is registered in the DRF settings:

```python
# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.core.exceptions.custom_exception_handler',
    # ...
}
```

## Using Error Responses

### Raising Validation Errors

For validation errors, you can use DRF's `ValidationError`:

```python
from rest_framework.exceptions import ValidationError

def validate_resource(data):
    if data['status'] not in ['active', 'inactive']:
        raise ValidationError({
            'status': ['Status must be either "active" or "inactive"']
        })
```

### Raising Permission Errors

For permission errors, use DRF's `PermissionDenied`:

```python
from rest_framework.exceptions import PermissionDenied

def check_permission(user, resource):
    if not user_can_access(user, resource):
        raise PermissionDenied("You don't have permission to access this resource")
```

### Raising Not Found Errors

For not found errors, use DRF's `NotFound`:

```python
from rest_framework.exceptions import NotFound

def get_resource(id):
    try:
        return Resource.objects.get(id=id)
    except Resource.DoesNotExist:
        raise NotFound("Resource not found")
```

### Custom Error Responses

You can also create custom error responses using the `error_response` helper:

```python
from api.core.responses import error_response

def custom_error_view(request):
    return error_response(
        message="An error occurred",
        details={"field": ["Error details"]},
        status_code=400
    )
```

## Error Logging

All errors are automatically logged by the custom exception handler:

```python
def log_error(exc, context):
    """
    Log the error with additional context information.
    """
    request = context.get('request')
    view = context.get('view')
    
    logger.error(
        f"Error in {view.__class__.__name__}: {str(exc)}",
        extra={
            'user_id': getattr(request.user, 'id', None),
            'company_id': getattr(getattr(request.user, 'company', None), 'id', None),
            'view': view.__class__.__name__,
            'url': request.path,
            'method': request.method,
        },
        exc_info=True
    )
```

## Customizing Error Messages

To customize error messages for specific exceptions, you can override the `get_error_message` function:

```python
def get_error_message(exc):
    """
    Get a human-readable error message from the exception.
    """
    # Custom messages for specific exception types
    if isinstance(exc, ValidationError):
        return "Validation error"
    elif isinstance(exc, PermissionDenied):
        return "Permission denied"
    elif isinstance(exc, NotFound):
        return "Resource not found"
    
    # Default message
    return str(exc) or "An error occurred"
```

## Testing Error Handling

When testing your error handling, ensure you test:

1. Validation errors
2. Permission errors
3. Not found errors
4. Custom error responses

Example test:

```python
def test_validation_error(self):
    self.client.force_authenticate(user=self.user)
    url = reverse('resource-list')
    data = {
        'name': 'Test Resource',
        'status': 'invalid'  # Invalid status
    }
    response = self.client.post(url, data, format='json')
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertEqual(response.data['status'], 'error')
    self.assertIn('status', response.data['details'])
```

## Best Practices

1. **Consistent Error Format** - Always use the standard error response format
2. **Meaningful Messages** - Provide clear and descriptive error messages
3. **Detailed Information** - Include specific details about the error
4. **Proper Status Codes** - Use the appropriate HTTP status code for each error
5. **Log All Errors** - Ensure all errors are properly logged for debugging

By following these principles, you'll ensure a consistent and user-friendly error handling system across your API. 