"""
Utilities for the API module.
"""

def create_response(status, status_code, message=None, data=None, errors=None):
    """
    Creates a standardized response structure for API responses.
    
    Args:
        status (str): The status of the response ('success', 'error', etc.)
        status_code (int): The HTTP status code
        message (str, optional): A descriptive message about the response
        data (dict, optional): The data payload of the response
        errors (list, optional): A list of errors if any
        
    Returns:
        dict: A standardized response dictionary
    """
    response = {
        'status': status,
        'status_code': status_code,
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    if errors is not None:
        response['errors'] = errors
    
    return response

def get_tenant_from_request(request):
    """
    Get the tenant (company) from the request.
    
    The TenantContextMiddleware adds the company object to the request.
    This function is a convenient way to access it from views.
    
    Args:
        request: The HTTP request object
        
    Returns:
        The company object or None if not available
    """
    return getattr(request, 'company', None)

def get_client_ip(request):
    """
    Get the client IP address from the request.
    
    Args:
        request: The HTTP request object
        
    Returns:
        The client IP address as a string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip 