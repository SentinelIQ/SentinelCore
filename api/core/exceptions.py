from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from .responses import error_response
import logging

logger = logging.getLogger('api.exceptions')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all API error responses consistently.
    
    Args:
        exc: The exception instance
        context: The exception context containing request and view information
        
    Returns:
        A standardized error response using our API response format
    """
    # First try the default handler to get the response
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the exception
        logger.error(
            f"API Error: {exc} - View: {context['view'].__class__.__name__} - "
            f"Method: {context['request'].method} - Path: {context['request'].path}"
        )
        
        # Extract error details
        error_data = None
        if hasattr(response, 'data'):
            error_data = response.data
        
        # Use our standardized error response
        message = str(exc)
        
        # Create a standardized error response
        return error_response(
            message=message,
            errors=error_data,
            code=response.status_code,
            status_code=response.status_code
        )
    
    # For unhandled exceptions, log them and return a generic 500 error
    logger.exception(
        f"Unhandled Exception: {exc} - View: {context['view'].__class__.__name__} - "
        f"Method: {context['request'].method} - Path: {context['request'].path}"
    )
    
    return error_response(
        message="An unexpected error occurred.",
        code="server_error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    ) 