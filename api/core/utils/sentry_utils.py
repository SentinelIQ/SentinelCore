"""
Utility functions for using Sentry in background tasks and services.
These utilities make it easier to include context and trace errors in non-request scenarios.
"""

import functools
import uuid
import logging
import traceback
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)


def with_sentry_context(service_name: str) -> Callable:
    """
    Decorator that adds Sentry context to background tasks or services.
    
    Args:
        service_name: A name identifying the service or task category
        
    Returns:
        Decorator function to wrap the target function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Import Sentry only if available
                from sentineliq.sentry import set_context, set_transaction
                
                # Generate a unique ID for this operation
                operation_id = str(uuid.uuid4())
                
                # Set transaction name
                transaction_name = f"{service_name}.{func.__name__}"
                set_transaction(transaction_name)
                
                # Set context for this operation
                set_context("background_operation", {
                    "operation_id": operation_id,
                    "service": service_name,
                    "function": func.__name__,
                })
                
                # Add args/kwargs if they might be useful
                # Be careful not to include sensitive data
                set_context("operation_details", {
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                })
                
                # Call the original function
                return func(*args, **kwargs)
            except ImportError:
                # Sentry not available, just call the function
                return func(*args, **kwargs)
            except Exception:
                # Let the exception propagate but it should be caught by Sentry
                raise
                
        return wrapper
    return decorator


def capture_errors(service_name: str, 
                  reraise: bool = True,
                  extra_context: Optional[Dict[str, Any]] = None) -> Callable:
    """
    Decorator that catches and reports exceptions to Sentry.
    
    Args:
        service_name: A name identifying the service
        reraise: Whether to reraise the caught exception
        extra_context: Additional context data to include
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Call the original function
                return func(*args, **kwargs)
            except Exception as e:
                try:
                    # Try to report to Sentry
                    from sentineliq.sentry import set_context, capture_message
                    
                    # Add context
                    set_context("error_context", {
                        "service": service_name,
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                    })
                    
                    # Add any extra context
                    if extra_context:
                        set_context("extra_data", extra_context)
                    
                    # Add stack trace
                    set_context("stack_trace", {
                        "traceback": traceback.format_exc(),
                    })
                    
                    # Log the error with special message
                    capture_message(
                        f"Error in {service_name}.{func.__name__}: {str(e)}", 
                        level="error"
                    )
                    
                    logger.error(f"Error in {service_name}.{func.__name__}: {str(e)}")
                except ImportError:
                    # Sentry not available, just log
                    logger.exception(f"Error in {service_name}.{func.__name__}")
                
                # Reraise or swallow the exception
                if reraise:
                    raise
                return None
                
        return wrapper
    return decorator 