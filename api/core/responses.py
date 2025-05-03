from rest_framework.response import Response
from rest_framework import status


def standard_response(data=None, message=None, status_type="success", metadata=None, code=None):
    """
    Create a standardized API response that ensures consistent format across all endpoints.
    
    Args:
        data: The main response data (can be a dict, list, or any serializable object)
        message: Optional message providing additional context about the response
        status_type: Response status indicator ("success", "error", "warning")
        metadata: Additional metadata like pagination details or processing information
        code: Custom code for more specific status identification
        
    Returns:
        Dict with standardized structure
    """
    response = {
        "status": status_type,
    }
    
    # Only include data if it's provided and not None
    if data is not None:
        response["data"] = data
        
    if message:
        response["message"] = message
        
    if code:
        response["code"] = code
        
    if metadata:
        response["metadata"] = metadata
        
    return response


class StandardResponse(Response):
    """
    Enhanced Response class that automatically formats the response data
    according to our API standards.
    """
    def __init__(self, data=None, message=None, status_type="success", 
                 metadata=None, code=None, status_code=status.HTTP_200_OK, **kwargs):
        """
        Create a standardized response object.
        
        Args:
            data: The main response data
            message: Optional context message
            status_type: Response status indicator ("success", "error", "warning")
            metadata: Additional metadata like pagination
            code: Custom code for more specific status identification
            status_code: HTTP status code
            **kwargs: Additional arguments for the Response class
        """
        formatted_data = standard_response(
            data=data,
            message=message,
            status_type=status_type,
            metadata=metadata,
            code=code
        )
        super().__init__(data=formatted_data, status=status_code, **kwargs)


# Convenience methods for different response types
def success_response(data=None, message=None, metadata=None, status_code=status.HTTP_200_OK, **kwargs):
    """Shortcut for successful responses"""
    return StandardResponse(
        data=data, 
        message=message, 
        status_type="success", 
        metadata=metadata, 
        status_code=status_code, 
        **kwargs
    )


def error_response(message, errors=None, code=None, metadata=None, status_code=status.HTTP_400_BAD_REQUEST, **kwargs):
    """Shortcut for error responses"""
    return StandardResponse(
        data=errors, 
        message=message, 
        status_type="error", 
        code=code,
        metadata=metadata, 
        status_code=status_code, 
        **kwargs
    )


def created_response(data=None, message=None, metadata=None, **kwargs):
    """Shortcut for created responses"""
    return success_response(
        data=data, 
        message=message or "Resource created successfully", 
        metadata=metadata, 
        status_code=status.HTTP_201_CREATED, 
        **kwargs
    )


def no_content_response(**kwargs):
    """Shortcut for no content responses"""
    return StandardResponse(status_code=status.HTTP_204_NO_CONTENT, **kwargs) 