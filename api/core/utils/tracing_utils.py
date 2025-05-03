"""
Stub module for backward compatibility.
This module previously contained Jaeger tracing utilities.
These functions now do nothing but are kept for import compatibility.
"""

import functools
import logging
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)


def trace_task(task_type: str) -> Callable:
    """
    No-op decorator that previously added Jaeger tracing to Celery tasks.
    
    Args:
        task_type: A name identifying the type of task
        
    Returns:
        Decorator function that now just passes through the original function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def create_child_span(parent_span, name: str, tags: Optional[Dict[str, Any]] = None):
    """
    No-op function that previously created a child span from a parent span.
    
    Returns:
        None
    """
    return None


# Add this to a Celery task for tracing
# Example usage:
# @app.task
# @trace_task("data_processing")
# def process_data(data_id):
#     # Task implementation here
#     pass 