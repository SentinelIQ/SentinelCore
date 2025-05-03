from drf_spectacular.utils import OpenApiExample
from .responses import standard_response


def get_examples(examples_request, **kwargs):
    """
    Factory function for generating standardized API response examples.
    
    This function helps DRF Spectacular generate example responses in the standardized format.
    
    Args:
        examples_request: The examples request context from DRF Spectacular
        
    Returns:
        Dictionary of example responses
    """
    operation_id = examples_request.get("operation_id", "")
    
    # Example responses by operation pattern
    examples = {}
    
    # User examples
    if operation_id.startswith("user_"):
        if "list" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data=[
                        {
                            "id": 1,
                            "username": "admin@example.com",
                            "email": "admin@example.com",
                            "first_name": "Admin",
                            "last_name": "User",
                            "company": {
                                "id": 1,
                                "name": "Example Company"
                            },
                            "is_active": True,
                            "is_superuser": True,
                            "is_admin_company": False,
                            "is_analyst_company": False,
                            "date_joined": "2023-05-15T10:00:00Z"
                        }
                    ],
                    metadata={
                        "pagination": {
                            "count": 1,
                            "page": 1,
                            "pages": 1,
                            "page_size": 50,
                            "next": None,
                            "previous": None
                        }
                    }
                )
            )
        elif "retrieve" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data={
                        "id": 1,
                        "username": "admin@example.com",
                        "email": "admin@example.com",
                        "first_name": "Admin",
                        "last_name": "User",
                        "company": {
                            "id": 1,
                            "name": "Example Company"
                        },
                        "is_active": True,
                        "is_superuser": True,
                        "is_admin_company": False,
                        "is_analyst_company": False,
                        "date_joined": "2023-05-15T10:00:00Z"
                    }
                )
            )
    
    # Company examples
    elif operation_id.startswith("company_"):
        if "list" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data=[
                        {
                            "id": 1,
                            "name": "Example Company",
                            "created_at": "2023-05-15T10:00:00Z",
                            "updated_at": "2023-05-15T10:00:00Z"
                        }
                    ],
                    metadata={
                        "pagination": {
                            "count": 1,
                            "page": 1,
                            "pages": 1,
                            "page_size": 50,
                            "next": None,
                            "previous": None
                        }
                    }
                )
            )
    
    # Authentication examples
    elif operation_id.startswith("token_"):
        if "obtain" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": 1,
                            "username": "admin@example.com",
                            "email": "admin@example.com",
                            "first_name": "Admin",
                            "last_name": "User"
                        }
                    },
                    message="Authentication successful"
                )
            )
        elif "refresh" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    },
                    message="Token refreshed successfully"
                )
            )
    
    # Default error responses
    examples["400"] = OpenApiExample(
        name="Validation Error",
        value=standard_response(
            status_type="error",
            message="Invalid data provided",
            data={
                "field_name": [
                    "Error message about this field"
                ]
            },
            code=400
        )
    )
    
    examples["401"] = OpenApiExample(
        name="Unauthorized",
        value=standard_response(
            status_type="error",
            message="Authentication credentials were not provided or are invalid",
            code=401
        )
    )
    
    examples["403"] = OpenApiExample(
        name="Forbidden",
        value=standard_response(
            status_type="error",
            message="You do not have permission to perform this action",
            code=403
        )
    )
    
    examples["404"] = OpenApiExample(
        name="Not Found",
        value=standard_response(
            status_type="error",
            message="The requested resource was not found",
            code=404
        )
    )
    
    examples["500"] = OpenApiExample(
        name="Server Error",
        value=standard_response(
            status_type="error",
            message="An unexpected error occurred",
            code="server_error"
        )
    )
    
    return examples 