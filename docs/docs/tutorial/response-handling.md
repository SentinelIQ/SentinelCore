---
sidebar_position: 4
---

# Response Handling

SentinelIQ implements a standardized response format across all API endpoints. This guide explains how to use the response handling system.

## Standardized Response Format

All API responses in SentinelIQ follow a consistent format:

```json
{
  "status": "success", // or "error"
  "data": {}, // Response data (for success responses)
  "message": "Operation completed successfully", // Human-readable message
  "meta": { // Additional metadata
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_pages": 5,
      "total_records": 42
    }
  }
}
```

This format ensures consistency across all endpoints and makes it easier for clients to process responses.

## Response Helper Functions

SentinelIQ provides several helper functions in the `api.core.responses` module to generate standardized responses:

### Success Response

Use `success_response()` for general success responses (HTTP 200):

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

### Created Response

Use `created_response()` for resource creation (HTTP 201):

```python
from api.core.responses import created_response

def create_resource(request):
    serializer = ResourceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    resource = serializer.save()
    return created_response(
        data=serializer.data,
        message="Resource created successfully"
    )
```

### No Content Response

Use `no_content_response()` for successful operations without a response body (HTTP 204):

```python
from api.core.responses import no_content_response

def delete_resource(request, id):
    resource = get_object_or_404(Resource, id=id)
    resource.delete()
    return no_content_response(
        message="Resource deleted successfully"
    )
```

### Error Response

Use `error_response()` for error responses:

```python
from api.core.responses import error_response

def custom_action(request):
    if not validate_request(request):
        return error_response(
            message="Invalid request parameters",
            details={"param": "Invalid value"},
            status_code=400
        )
    # Process request...
```

## Integration with ViewSets

When using ViewSets, you should override the default methods to use these response helpers:

```python
from api.core.responses import success_response, created_response, no_content_response
from rest_framework import viewsets

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Resources retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        return created_response(
            data=serializer.data,
            message="Resource created successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Resource retrieved successfully"
        )
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(
            data=serializer.data,
            message="Resource updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return no_content_response(
            message="Resource deleted successfully"
        )
```

## Using with Mixins

When using the modular view structure with mixins, each mixin should handle its own response formatting:

```python
# resource_create.py
from api.core.responses import created_response

class ResourceCreateMixin:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Audit logging
        self.log_action('create', instance)
        
        return created_response(
            data=serializer.data,
            message="Resource created successfully"
        )
```

## Pagination Integration

The response format also integrates with pagination:

```python
from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response

class CustomPaginationClass(StandardResultsSetPagination):
    def get_paginated_response(self, data):
        return success_response(
            data=data,
            message="Resources retrieved successfully",
            meta={
                "pagination": {
                    'page': self.page.number,
                    'page_size': self.page_size,
                    'total_pages': self.page.paginator.num_pages,
                    'total_records': self.page.paginator.count,
                }
            }
        )
```

## Error Handling Integration

The standardized response format is also integrated with the error handling system:

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
    
    return response
```

This ensures that all error responses also follow the standardized format.

## Best Practices

1. **Always Use Response Helpers** - Never return a raw DRF response; always use the helpers
2. **Include Meaningful Messages** - Provide clear and descriptive messages
3. **Use Appropriate Status Codes** - Use the correct response type for each operation
4. **Standardize Error Details** - Structure error details consistently
5. **Include Pagination Metadata** - Always include pagination information for list endpoints

In the next section, we'll explore the [RBAC system](rbac-basics) for implementing role-based access control. 