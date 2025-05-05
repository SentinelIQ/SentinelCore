"""
Middleware for logging request information to help with debugging and auditing.

This middleware records information about each request and logs it
at different log levels depending on status codes and settings.
"""

import logging
import json
import time
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

# Create a specific logger for request logging
logger = logging.getLogger('request')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs request information.
    
    Logs information such as:
    - Request method and URL
    - Status code
    - Processing time
    - Request data (for non-GET methods)
    """
    
    def process_request(self, request):
        """Process request and store start time."""
        request.start_time = time.time()
    
    def process_response(self, request, response):
        """Process response and log request information."""
        # Skip logging for excluded paths
        if hasattr(settings, 'REQUEST_LOGGING_EXCLUDE_PATHS'):
            for path in settings.REQUEST_LOGGING_EXCLUDE_PATHS:
                if request.path.startswith(path):
                    return response
        
        # Calculate request processing time
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            duration_str = f"{duration:.3f}s"
        else:
            duration_str = "unknown"
        
        # Prepare log data
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': duration_str,
            'ip': self.get_client_ip(request),
        }
        
        # Add user info if available
        if hasattr(request, 'user') and request.user.is_authenticated:
            log_data['user'] = request.user.username
        
        # Add request body for non-GET requests (excluding files)
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            try:
                if request.content_type and 'application/json' in request.content_type:
                    if hasattr(request, 'body') and request.body:
                        body_data = json.loads(request.body.decode('utf-8'))
                        # Sanitize sensitive data
                        sanitized_data = self._sanitize_data(body_data)
                        log_data['body'] = sanitized_data
                elif hasattr(request, 'POST') and request.POST:
                    post_data = dict(request.POST.items())
                    sanitized_data = self._sanitize_data(post_data)
                    log_data['body'] = sanitized_data
            except (ValueError, json.JSONDecodeError):
                log_data['body'] = 'Error parsing request body'
        
        # Choose log level based on status code
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
        
        return response
    
    def get_client_ip(self, request):
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get first IP in chain of proxies
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _sanitize_data(self, data):
        """Remove sensitive information from request data."""
        if not isinstance(data, dict):
            return data
            
        sanitized = data.copy()
        sensitive_fields = ['password', 'token', 'key', 'secret', 'authorization']
        
        for field in sanitized:
            if any(s in field.lower() for s in sensitive_fields):
                sanitized[field] = "****MASKED****"
            elif isinstance(sanitized[field], dict):
                sanitized[field] = self._sanitize_data(sanitized[field])
        
        return sanitized 