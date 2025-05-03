"""
Utility functions for handling multi-tenancy (companies).
"""
from rest_framework.exceptions import PermissionDenied


def get_tenant_from_request(request):
    """
    Get the tenant (company) from the request.
    
    This function extracts the company from the authenticated user's request
    and ensures the user has proper access rights.
    
    Args:
        request: The HTTP request object
        
    Returns:
        Company: The company object for the current request
        
    Raises:
        PermissionDenied: If the user doesn't have access to a company
    """
    # Ensure user is authenticated
    if not request.user or not request.user.is_authenticated:
        raise PermissionDenied("Authentication required to determine tenant")
    
    # Get company from user
    company = getattr(request.user, 'company', None)
    
    # For superusers without a company, we can't determine the tenant
    # This should be handled by the calling view to set an appropriate
    # company context (if needed for superuser operations)
    if not company and not request.user.is_superuser:
        raise PermissionDenied("User doesn't have access to a company")
    
    return company 