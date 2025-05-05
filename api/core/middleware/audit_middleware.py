"""
Enhanced Audit Log Middleware.

Extends the standard AuditlogMiddleware to:
1. Log user authentication events
2. Log API access
3. Record API access
4. Provide additional context
"""

import threading
import logging
import json
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import resolve
from auditlog.middleware import AuditlogMiddleware
from auditlog.models import LogEntry
from api.core.audit import log_api_access, log_api_view

logger = logging.getLogger('auditlog')

# Thread local to store current request data
_thread_locals = threading.local()

User = get_user_model()


class EnhancedAuditlogMiddleware(AuditlogMiddleware):
    """
    Middleware that extends the standard AuditlogMiddleware from django-auditlog.
    
    Adds features:
    1. User authentication events
    2. API access logs
    3. Request context
    4. Request data
    """
    
    def process_request(self, request):
        """
        Process the request and store context information.
        """
        # Call original implementation
        result = super().process_request(request)
        
        try:
            # Store request information for later use in process_response
            _thread_locals.request = request
            
            # Extract basic request data
            request_data = {
                'request_method': request.method,
                'request_path': request.path,
                'client_ip': self.get_client_ip(request),
                'timestamp': timezone.now().isoformat()
            }
            
            # Extract request body data, only for non-GET methods
            if request.method not in ('GET', 'HEAD', 'OPTIONS'):
                try:
                    # Try to get JSON data first
                    if request.content_type == 'application/json':
                        if hasattr(request, 'body') and request.body:
                            data = json.loads(request.body)
                            # Filter out sensitive data
                            if isinstance(data, dict):
                                if 'password' in data:
                                    data['password'] = '******'
                                if 'token' in data:
                                    data['token'] = '******'
                            request_data['request_data'] = data
                    # If not JSON, capture form data (if any)
                    elif request.content_type == 'application/x-www-form-urlencoded':
                        request_data['request_data'] = {k: v for k, v in request.POST.items()}
                except Exception as e:
                    logger.debug(f"Could not parse request body: {str(e)}")
            
            # Store request data in thread locals
            _thread_locals.request_data = request_data
                    
        except Exception as e:
            # In case of error, don't store request data
            logger.error(f"Error in audit middleware process_request: {str(e)}")
        
        return result
    
    def process_response(self, request, response):
        """
        Process the response and record audit information.
        """
        # Get the original implementation result
        result = super().process_response(request, response)
        
        try:
            # Get request data from thread locals
            request_data = getattr(_thread_locals, 'request_data', {})
            
            # Add response status
            request_data['response_status'] = response.status_code
            
            # Get resolved view information
            try:
                resolved = resolve(request.path)
                view_name = f"{resolved.func.__module__}.{resolved.func.__name__}"
                request_data['view_name'] = view_name
                request_data['view_args'] = resolved.args
                request_data['view_kwargs'] = resolved.kwargs
            except Exception:
                # If URL is not resolved, we can't extract view info
                pass
            
            # Check if we have a user
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            
            # Record response status
            if 'response_status' not in request_data:
                request_data['response_status'] = response.status_code
            
            # Calculate request duration
            if 'timestamp' in request_data:
                start_time = timezone.datetime.fromisoformat(request_data['timestamp'])
                end_time = timezone.now()
                duration = (end_time - start_time).total_seconds()
                request_data['duration_seconds'] = duration
            
            # Log API access for GET methods
            if request.method == 'GET':
                # Only log GET requests to actual views (not static files, etc.)
                if 'view_name' in request_data:
                    log_api_access(
                        user=user,
                        method=request.method,
                        path=request.path,
                        status_code=response.status_code,
                        additional_data=request_data
                    )
            
            # Log view if not already captured
            # This is for cases where a view function doesn't do model operations
            # that would trigger LogEntry creation
            if request.method != 'GET' and 'view_name' in request_data:
                try:
                    # Check if we already have a log entry for this view
                    # through the standard AuditlogMiddleware
                    if not self._has_recent_log_entry(user, request.path):
                        log_api_view(
                            user=user,
                            method=request.method,
                            path=request.path,
                            status_code=response.status_code,
                            additional_data=request_data
                        )
                except Exception as e:
                    # Log view
                    logger.debug(f"Error checking for existing log entry: {str(e)}")
            
        except Exception as e:
            # If there is an error logging the access, just log the error
            logger.error(f"Error logging API access: {str(e)}")
        
        return result
    
    def _has_recent_log_entry(self, user, path, window_seconds=5):
        """
        Check if there is a recent log entry for this user and path.
        
        Args:
            user: The user object
            path: The request path
            window_seconds: Window in seconds to check for recent entries
            
        Returns:
            bool: True if there is a recent entry, False otherwise
        """
        if not user:
            return False
            
        # Get the cutoff time
        cutoff_time = timezone.now() - timezone.timedelta(seconds=window_seconds)
        
        # Check for recent entries
        return LogEntry.objects.filter(
            actor=user,
            additional_data__request_path=path,
            timestamp__gte=cutoff_time
        ).exists()
    
    def get_client_ip(self, request):
        """
        Get client IP from request.
        
        Tries various headers to find the real client IP,
        accounting for proxies and load balancers.
        
        Args:
            request: The HTTP request
            
        Returns:
            str: The client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip 