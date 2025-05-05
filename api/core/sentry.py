"""
Enhanced Sentry integration for API Core.

This module extends the base Sentry configuration with API-specific features
including performance monitoring, context enrichment, and error tracking
specifically designed for the REST API ecosystem.
"""

import inspect
import functools
import logging
import time
import uuid
import json
from typing import Callable, Dict, Any, Optional, Union, List
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

logger = logging.getLogger('api.sentry')

# Import base Sentry functions, or create no-op functions if Sentry isn't available
try:
    from sentineliq.sentry import (
        set_user, set_context, set_transaction, 
        capture_message, setup_sentry
    )
    SENTRY_AVAILABLE = True
except ImportError:
    # Define no-op functions when Sentry is not available
    def set_user(user_info): pass
    def set_context(name, data): pass
    def set_transaction(name): pass
    def capture_message(message, **kwargs): pass
    def setup_sentry(): pass
    
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not available, monitoring features disabled")


def initialize_api_monitoring():
    """
    Initialize API-specific monitoring in Sentry.
    
    This function should be called during Django startup to set up
    API-specific Sentry configurations and tags.
    """
    if not SENTRY_AVAILABLE:
        return
    
    # Set global tags for API monitoring
    set_context("api_monitoring", {
        "version": getattr(settings, 'API_VERSION', 'v1'),
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "monitoring_enabled": True,
    })
    
    # Add API-specific tags
    from sentineliq.sentry import sentry_sdk
    sentry_sdk.set_tag("component", "api")
    
    logger.info("API monitoring initialized in Sentry")


def monitor_api_view(view_func=None, name=None, include_params=False):
    """
    Decorator to monitor API view performance and errors with Sentry.
    
    Args:
        view_func: The view function to decorate
        name: Custom name for the transaction (defaults to view function name)
        include_params: Whether to include request parameters in Sentry context
        
    Returns:
        Decorated function with Sentry monitoring
    """
    def actual_decorator(f):
        @functools.wraps(f)
        def wrapper(self, request, *args, **kwargs):
            if not SENTRY_AVAILABLE:
                return f(self, request, *args, **kwargs)
            
            # Generate a unique ID for this request
            request_id = getattr(request, 'request_id', str(uuid.uuid4()))
            
            # Get view name
            view_name = name
            if not view_name:
                # Try to get a descriptive name
                if hasattr(self, '__class__'):
                    view_name = f"{self.__class__.__name__}.{f.__name__}"
                else:
                    view_name = f.__name__
            
            # Start transaction
            set_transaction(f"api.{view_name}")
            
            # Set basic context
            set_context("api_request", {
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "view": view_name,
            })
            
            # Add request parameters if enabled
            if include_params:
                # Filter out sensitive data
                query_params = _sanitize_data(dict(request.GET.items()))
                
                # Add to context
                set_context("request_params", {
                    "query_params": query_params,
                    # Only include safe fields from POST/data
                    "body_params": _get_safe_request_body(request),
                })
            
            # Record authentication info
            if hasattr(request, 'user') and request.user.is_authenticated:
                set_user({
                    "id": str(request.user.id),
                    "username": request.user.username,
                    "email": request.user.email,
                })
                
                # If user has a company, add tenant context
                if hasattr(request.user, 'company') and request.user.company:
                    set_context("tenant", {
                        "company_id": str(request.user.company.id),
                        "company_name": request.user.company.name
                    })
            
            # Track performance
            start_time = time.time()
            try:
                # Execute the view function
                response = f(self, request, *args, **kwargs)
                
                # Add response data
                duration = time.time() - start_time
                status_code = getattr(response, 'status_code', 200)
                
                set_context("api_response", {
                    "status_code": status_code,
                    "duration_ms": int(duration * 1000),
                    "success": 200 <= status_code < 400,
                })
                
                return response
            except Exception as exc:
                # Add exception context
                duration = time.time() - start_time
                
                set_context("api_error", {
                    "duration_ms": int(duration * 1000),
                    "exception_type": type(exc).__name__,
                    "view": view_name,
                })
                
                # Re-raise the exception - Sentry will capture it
                raise
        
        return wrapper
    
    # Handle the case where decorator is used without parentheses
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def monitor_api_viewset(
    include_params: bool = False, 
    high_volume_actions: List[str] = None
):
    """
    Class decorator to monitor all ViewSet actions with Sentry.
    
    Args:
        include_params: Whether to include request parameters
        high_volume_actions: List of high-volume actions to sample at a lower rate
        
    Returns:
        Decorated ViewSet class
    """
    high_volume_actions = high_volume_actions or ['list']
    
    def decorator(viewset_class):
        # Only proceed if the class is a ViewSet
        if not (issubclass(viewset_class, ViewSet) or issubclass(viewset_class, APIView)):
            return viewset_class
        
        # Get all methods that could be action handlers
        for name, method in inspect.getmembers(viewset_class, inspect.isfunction):
            # Skip private/protected methods
            if name.startswith('_'):
                continue
                
            # Skip methods not from the class itself
            if method.__module__ != viewset_class.__module__:
                continue
            
            # Check if this is a high volume action (for sampling)
            is_high_volume = name in high_volume_actions
            
            # Decorate the method
            decorated_method = monitor_api_view(
                name=f"{viewset_class.__name__}.{name}",
                include_params=include_params
            )(method)
            
            # Replace the original method with the decorated one
            setattr(viewset_class, name, decorated_method)
            
        return viewset_class
    
    return decorator


def track_operation(operation_type: str, data: Dict[str, Any]):
    """
    Track an operation in Sentry for monitoring specific actions.
    
    Args:
        operation_type: Type of operation (e.g., 'create_alert', 'user_login')
        data: Data related to the operation (avoid sensitive information)
    """
    if not SENTRY_AVAILABLE:
        return
    
    # Create a unique operation ID
    operation_id = str(uuid.uuid4())
    
    # Set context
    set_context("tracked_operation", {
        "operation_id": operation_id,
        "operation_type": operation_type,
        "timestamp": time.time(),
        **data
    })
    
    # Log a message that will be captured by Sentry
    capture_message(
        f"Operation tracked: {operation_type}",
        level="info"
    )


def _sanitize_data(data):
    """
    Sanitize data to remove sensitive information.
    
    Args:
        data: Dictionary of data to sanitize
        
    Returns:
        Sanitized data with sensitive fields masked
    """
    if not data or not isinstance(data, dict):
        return data
        
    sanitized = data.copy()
    
    sensitive_fields = [
        'password', 'token', 'key', 'secret', 'credential',
        'api_key', 'auth', 'authorization', 'access_token',
        'refresh_token', 'private_key'
    ]
    
    for field, value in sanitized.items():
        # Check if field name contains sensitive keywords
        if any(sensitive in field.lower() for sensitive in sensitive_fields):
            sanitized[field] = "***FILTERED***"
        # Recursively sanitize nested dictionaries
        elif isinstance(value, dict):
            sanitized[field] = _sanitize_data(value)
    
    return sanitized


def _get_safe_request_body(request):
    """
    Get sanitized request body data for Sentry context.
    
    Args:
        request: The HTTP request
        
    Returns:
        Sanitized request body data or None
    """
    # Get request data safely
    if request.method not in ('GET', 'DELETE'):
        try:
            # For JSON data
            if hasattr(request, 'data') and request.data:
                return _sanitize_data(request.data)
            
            # For form data
            if hasattr(request, 'POST') and request.POST:
                return _sanitize_data(dict(request.POST.items()))
                
        except Exception:
            return {"error": "Could not parse request body"}
    
    return None


# Context manager for monitoring blocks of code
class SentrySpan:
    """
    Context manager to create a span in Sentry transactions.
    
    Example:
    ```python
    with SentrySpan("database_operation", description="Fetch alerts"):
        alerts = Alert.objects.filter(status='active')
    ```
    """
    
    def __init__(self, 
                 operation_name: str, 
                 description: Optional[str] = None,
                 data: Optional[Dict[str, Any]] = None):
        """
        Initialize the span.
        
        Args:
            operation_name: Name of the operation
            description: Description of what this span does
            data: Additional context data for the span
        """
        self.operation_name = operation_name
        self.description = description
        self.data = data or {}
        self.start_time = None
        self.span = None
        
    def __enter__(self):
        if not SENTRY_AVAILABLE:
            return self
            
        self.start_time = time.time()
        
        try:
            # Create a span in the current transaction
            from sentineliq.sentry import sentry_sdk
            
            transaction = sentry_sdk.Hub.current.scope.transaction
            if transaction:
                self.span = transaction.start_child(
                    op=self.operation_name,
                    description=self.description
                )
                
                # Add data
                if self.data:
                    for key, value in self.data.items():
                        self.span.set_data(key, value)
        except (ImportError, AttributeError):
            # Sentry not available or transaction doesn't exist
            pass
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not SENTRY_AVAILABLE:
            return
            
        # Record duration
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Finish the span if it exists
            if self.span:
                self.span.set_data("duration_ms", int(duration * 1000))
                self.span.finish()
                
        # Don't suppress exceptions
        return False 