"""
Integration between Django Audit Logs and Sentry.

This module connects the Django-Auditlog system with Sentry to provide
enhanced security monitoring, audit trail visibility, and anomaly detection
across the entire application.
"""

import logging
import functools
import uuid
from typing import Dict, Any, Optional, Callable

from django.conf import settings
from django.contrib.auth import get_user_model
from auditlog.models import LogEntry

User = get_user_model()
logger = logging.getLogger('audit.sentry')

# Import Sentry functions if available
try:
    from sentineliq.sentry import set_context, capture_message, set_tag, set_user
    SENTRY_AVAILABLE = True
except ImportError:
    # Define no-op functions if Sentry isn't available
    def set_context(name, data): pass
    def capture_message(message, **kwargs): pass
    def set_tag(key, value): pass
    def set_user(user_info): pass
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not available, audit-sentry integration disabled")


def initialize_audit_monitoring():
    """
    Initialize the audit monitoring integration with Sentry.
    This should be called during Django startup.
    """
    if not SENTRY_AVAILABLE:
        return
    
    # Set global tags for audit monitoring
    set_tag("audit_monitoring", "enabled")
    set_context("audit_config", {
        "version": getattr(settings, 'AUDIT_VERSION', '1.0'),
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
    })
    
    logger.info("Audit monitoring initialized in Sentry")


def monitor_security_events(action_types=None):
    """
    Monitor specific security events in the audit log.
    
    Args:
        action_types: List of action types to monitor (default: all)
    """
    if not SENTRY_AVAILABLE:
        return
    
    # Default to monitoring all security-relevant action types
    if action_types is None:
        action_types = [
            LogEntry.Action.CREATE,  # Creation events
            LogEntry.Action.UPDATE,  # Update events
            LogEntry.Action.DELETE,  # Deletion events 
        ]
    
    # Create a query manager
    from auditlog.models import LogEntry
    security_events = LogEntry.objects.filter(action__in=action_types)
    
    # Set up a signal handler to monitor new events
    from django.db.models.signals import post_save
    
    @functools.wraps(post_save)
    def log_entry_handler(sender, instance, created, **kwargs):
        if created and instance.action in action_types:
            # Process the security event
            _process_security_event(instance)
    
    # Connect the signal handler
    post_save.connect(log_entry_handler, sender=LogEntry)
    
    logger.info(f"Monitoring {len(action_types)} security event types in audit logs")


def track_audit_event(event_type: str, user=None, **data):
    """
    Track a security event in Sentry with relevant audit context.
    
    Args:
        event_type: Type of security event
        user: The user involved (if applicable)
        **data: Additional data to include with the event
    """
    if not SENTRY_AVAILABLE:
        return
    
    # Generate a unique event ID
    event_id = str(uuid.uuid4())
    
    # Set user context if provided
    if user:
        # For Django user model instances
        if hasattr(user, 'username'):
            set_user({
                "id": str(user.id),
                "username": user.username,
                "email": getattr(user, 'email', None)
            })
        # For user IDs
        elif isinstance(user, (str, int)):
            try:
                user_obj = User.objects.get(id=user)
                set_user({
                    "id": str(user_obj.id),
                    "username": user_obj.username,
                    "email": getattr(user_obj, 'email', None)
                })
            except User.DoesNotExist:
                set_user({"id": str(user)})
    
    # Set audit context
    set_context("audit_event", {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": data.get('timestamp', None),
        **data
    })
    
    # Set audit tag for easy filtering in Sentry
    set_tag("audit", event_type)
    
    # Send the event to Sentry
    capture_message(
        f"Audit event: {event_type}",
        level="info"  # Use info level for normal audit events
    )


def security_critical(event_name=None, level="warning"):
    """
    Decorator for functions that need security monitoring in Sentry.
    
    Args:
        event_name: Name of the security event
        level: Sentry level (warning, error)
        
    Returns:
        Decorated function with Sentry monitoring
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not SENTRY_AVAILABLE:
                return func(*args, **kwargs)
            
            # Determine the security event name
            security_event = event_name or f"{func.__module__}.{func.__name__}"
            
            # Get user from args or kwargs
            user = None
            for arg in args:
                if hasattr(arg, 'is_authenticated'):
                    user = arg
                    break
            
            if user is None and 'user' in kwargs:
                user = kwargs['user']
            
            # Start tracking
            set_tag("security_critical", "true")
            set_context("security_operation", {
                "function": func.__qualname__,
                "event": security_event,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            })
            
            # Set user context if available
            if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
                set_user({
                    "id": str(user.id),
                    "username": user.username,
                    "email": getattr(user, 'email', None)
                })
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Log successful execution
                capture_message(
                    f"Security operation completed: {security_event}",
                    level="info"
                )
                
                return result
            except Exception as e:
                # Add security incident context
                set_context("security_incident", {
                    "operation": security_event,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                })
                
                # Log security incident
                capture_message(
                    f"Security operation failed: {security_event}",
                    level=level
                )
                
                # Re-raise the exception
                raise
                
        return wrapper
    
    # Support using the decorator directly without parentheses
    if callable(event_name):
        func, event_name = event_name, None
        return decorator(func)
    
    return decorator


def _process_security_event(log_entry):
    """
    Process a security-relevant audit log entry and report to Sentry.
    
    Args:
        log_entry: The LogEntry instance from django-auditlog
    """
    if not SENTRY_AVAILABLE:
        return
    
    # Map action to readable name
    action_map = {
        LogEntry.Action.CREATE: 'created',
        LogEntry.Action.UPDATE: 'updated',
        LogEntry.Action.DELETE: 'deleted',
        LogEntry.Action.ACCESS: 'accessed',
    }
    
    action_name = action_map.get(log_entry.action, 'unknown')
    content_type = log_entry.content_type.model if log_entry.content_type else 'unknown'
    
    # Extract entity type from additional data if available
    entity_type = None
    if hasattr(log_entry, 'additional_data') and log_entry.additional_data:
        entity_type = log_entry.additional_data.get('entity_type', content_type)
    else:
        entity_type = content_type
    
    # Set Sentry context
    set_context("audit_log", {
        "id": str(log_entry.id),
        "action": action_name,
        "entity_type": entity_type,
        "entity_id": log_entry.object_pk,
        "timestamp": log_entry.timestamp.isoformat(),
        "changes": log_entry.changes,
    })
    
    # Set the user if available
    if log_entry.actor:
        set_user({
            "id": str(log_entry.actor.id),
            "username": log_entry.actor.username,
            "email": getattr(log_entry.actor, 'email', None)
        })
    
    # Set tags for filtering
    set_tag("audit_action", action_name)
    set_tag("entity_type", entity_type)
    
    # Determine message level based on action
    level = "info"
    if log_entry.action == LogEntry.Action.DELETE:
        level = "warning"  # Deletions are higher priority
    
    # Send to Sentry
    capture_message(
        f"Audit: {entity_type} {action_name} by {log_entry.actor}",
        level=level
    )


def detect_anomalies(lookback_hours=24, threshold=10):
    """
    Detect anomalies in the audit logs and report to Sentry.
    
    Args:
        lookback_hours: Hours to look back for anomaly detection
        threshold: Threshold for anomaly detection
    """
    if not SENTRY_AVAILABLE:
        return
    
    from django.utils import timezone
    import datetime
    
    # Calculate the lookback time
    lookback_time = timezone.now() - datetime.timedelta(hours=lookback_hours)
    
    # Get recent logs
    recent_logs = LogEntry.objects.filter(timestamp__gte=lookback_time)
    
    # Analyze logs for different patterns
    
    # 1. Excessive deletions
    delete_count = recent_logs.filter(action=LogEntry.Action.DELETE).count()
    if delete_count > threshold:
        set_context("anomaly_detection", {
            "type": "excessive_deletions",
            "count": delete_count,
            "threshold": threshold,
            "lookback_hours": lookback_hours,
        })
        
        capture_message(
            f"Security anomaly: Excessive deletions detected ({delete_count} in {lookback_hours}h)",
            level="warning"
        )
    
    # 2. Unusual activity by user
    user_actions = {}
    for log in recent_logs:
        if log.actor:
            user_id = str(log.actor.id)
            user_actions[user_id] = user_actions.get(user_id, 0) + 1
    
    # Find users with excessive actions
    for user_id, count in user_actions.items():
        if count > threshold * 2:  # Higher threshold for user actions
            try:
                user = User.objects.get(id=user_id)
                username = user.username
            except User.DoesNotExist:
                username = f"Unknown (ID: {user_id})"
                
            set_context("anomaly_detection", {
                "type": "excessive_user_activity",
                "user_id": user_id,
                "username": username,
                "action_count": count,
                "threshold": threshold * 2,
                "lookback_hours": lookback_hours,
            })
            
            capture_message(
                f"Security anomaly: Excessive activity by user {username} ({count} actions in {lookback_hours}h)",
                level="warning"
            ) 