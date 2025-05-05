---
sidebar_position: 3
---

# Response Format Reference

SentinelIQ implements a standardized response format across all API endpoints. This reference documents the structure and usage of these response formats.

## Standard Response Structure

All API responses in SentinelIQ follow this consistent format:

```json
{
  "status": "success",
  "data": {},
  "message": "Operation completed successfully",
  "meta": {
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_pages": 5,
      "total_records": 42
    }
  }
}
```

### Fields Explanation

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Response status, either "success" or "error" |
| `data` | object/array | The response payload (omitted for some response types) |
| `message` | string | Human-readable message describing the result |
| `meta` | object | Additional metadata about the response |
| `meta.pagination` | object | Pagination information for list endpoints |

## Success Response Types

### Standard Success (200 OK)

Used for general success responses, typically for GET requests and most operations.

```json
{
  "status": "success",
  "data": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Example Resource",
    "created_at": "2023-06-15T08:30:00Z"
  },
  "message": "Resource retrieved successfully"
}
```

### Created Response (201 Created)

Used when a new resource has been created, typically for POST requests.

```json
{
  "status": "success",
  "data": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "New Resource",
    "created_at": "2023-06-15T08:30:00Z"
  },
  "message": "Resource created successfully"
}
```

### No Content Response (204 No Content)

Used when an operation succeeded but no content is returned, typically for DELETE requests.

```json
{
  "status": "success",
  "message": "Resource deleted successfully"
}
```

### List Response with Pagination

Used for endpoints that return collections of resources.

```json
{
  "status": "success",
  "data": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "name": "Resource 1"
    },
    {
      "id": "a47ac10b-58cc-4372-a567-0e02b2c3d480",
      "name": "Resource 2"
    }
  ],
  "message": "Resources retrieved successfully",
  "meta": {
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_pages": 5,
      "total_records": 42
    }
  }
}
```

## Error Response Types

### Validation Error (400 Bad Request)

Used when request validation fails.

```json
{
  "status": "error",
  "message": "Validation error",
  "details": {
    "name": ["This field is required"],
    "email": ["Enter a valid email address"]
  },
  "code": 400
}
```

### Authentication Error (401 Unauthorized)

Used when authentication is required but not provided or invalid.

```json
{
  "status": "error",
  "message": "Authentication credentials were not provided",
  "code": 401
}
```

### Permission Error (403 Forbidden)

Used when the user is authenticated but doesn't have permission.

```json
{
  "status": "error",
  "message": "You do not have permission to perform this action",
  "code": 403
}
```

### Not Found Error (404 Not Found)

Used when the requested resource doesn't exist.

```json
{
  "status": "error",
  "message": "Resource not found",
  "code": 404
}
```

### Method Not Allowed Error (405 Method Not Allowed)

Used when the HTTP method is not supported for the endpoint.

```json
{
  "status": "error",
  "message": "Method not allowed",
  "code": 405
}
```

### Server Error (500 Internal Server Error)

Used for unexpected server errors.

```json
{
  "status": "error",
  "message": "An unexpected error occurred",
  "code": 500
}
```

## Response Generation

In code, responses are generated using helper functions from the `api.core.responses` module:

```python
from api.core.responses import (
    success_response,
    created_response,
    error_response,
    no_content_response
)

# Success response
def get_resource(request, id):
    resource = get_object_or_404(Resource, id=id)
    serializer = ResourceSerializer(resource)
    return success_response(
        data=serializer.data,
        message="Resource retrieved successfully"
    )

# Created response
def create_resource(request):
    serializer = ResourceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    resource = serializer.save()
    return created_response(
        data=serializer.data,
        message="Resource created successfully"
    )

# Error response
def custom_action(request):
    if not validate_request(request):
        return error_response(
            message="Invalid request",
            details={"field": "Error details"},
            status_code=400
        )
    # Process request...

# No content response
def delete_resource(request, id):
    resource = get_object_or_404(Resource, id=id)
    resource.delete()
    return no_content_response(
        message="Resource deleted successfully"
    )
```

## Best Practices

1. **Consistent Usage** - Always use the response helpers, never return raw responses
2. **Descriptive Messages** - Provide clear and descriptive messages
3. **Appropriate Status Codes** - Use the correct status code for each situation
4. **Pagination Metadata** - Include pagination information for all list endpoints
5. **Detailed Error Information** - Provide specific details for error responses

## Client Handling

Clients should first check the `status` field to determine if the request was successful:

```javascript
// JavaScript example
fetch('/api/resources/123')
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      // Handle success
      console.log(data.data);
    } else {
      // Handle error
      console.error(data.message, data.details);
    }
  });
``` 