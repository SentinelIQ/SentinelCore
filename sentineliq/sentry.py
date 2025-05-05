"""
Sentry configuration module for SentinelIQ.
This handles error reporting and performance monitoring for both Django and Celery.
"""

import os
import logging
from django.conf import settings
import django.db.models.signals

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


logger = logging.getLogger('sentry')


def get_release():
    """
    Get the current release version from environment or git.
    This helps to track which version of the application is generating errors.
    """
    # First check environment variable
    if release := os.environ.get('SENTRY_RELEASE'):
        return release
    
    # Try to get from Git if available
    try:
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
    except (ImportError, subprocess.SubprocessError):
        return None


def get_environment():
    """Get the current environment name."""
    return getattr(settings, 'ENVIRONMENT', 'development')


def setup_sentry():
    """
    Initialize and configure Sentry for the application.
    """
    environment = get_environment()
    dsn = os.environ.get('SENTRY_DSN')
    
    # Don't configure Sentry if no DSN is provided
    if not dsn:
        logger.warning("Sentry DSN not found in environment variables. Skipping Sentry initialization.")
        return
    
    # Set sampling rates based on environment
    # Use lower rates in production to manage volume
    if environment == 'production':
        traces_sample_rate = 0.1  # Sample 10% of transactions in production
        profiles_sample_rate = 0.05  # Profile 5% of sessions in production
    elif environment == 'staging':
        traces_sample_rate = 0.3  # Sample 30% of transactions in staging
        profiles_sample_rate = 0.1  # Profile 10% of sessions in staging
    else:  # development 
        traces_sample_rate = 1.0  # Sample all transactions in development
        profiles_sample_rate = 0.3  # Profile 30% of sessions in development

    # Configure logging integration - capture all errors and warnings
    sentry_logging = LoggingIntegration(
        level=logging.INFO,      # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    
    # Initialize Sentry SDK with explicit integrations and no automatic discovery
    # This avoids the problematic Tornado integration
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
                signals_denylist=[
                    django.db.models.signals.pre_init,
                    django.db.models.signals.post_init,
                ],
                cache_spans=True,
                http_methods_to_capture=("CONNECT", "DELETE", "GET", "PATCH", "POST", "PUT", "TRACE"),
            ),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
            sentry_logging,
        ],
        # Don't use default integrations to avoid Tornado integration issues
        default_integrations=False,
        
        # Environment to help separate staging/dev/prod
        environment=environment,
        # Release to track which version of code generates errors
        release=get_release(),
        
        # Performance monitoring settings
        traces_sample_rate=traces_sample_rate,
        # Profile session sampling rate
        profiles_sample_rate=profiles_sample_rate,
        # Link profiling to traces
        profile_lifecycle="trace",
        
        # Data capturing and filtering settings
        send_default_pii=True,  # Include user data with errors
        # Don't include local variables in stack traces (for security)
        include_local_variables=False,
        # Set max breadcrumbs to balance detail vs payload size
        max_breadcrumbs=50,
        
        # Before-send function for filtering/modifying events
        before_send=before_send,
        # Hooks for transaction data
        before_breadcrumb=before_breadcrumb,
        
        # Attach the request from signals/background tasks
        auto_session_tracking=True,
        # Controls source map and frame inspection
        enable_tracing=True,
        
        # Controls IP address collection - set to True if needed
        send_client_reports=True,
    )
    
    # Set up additional context
    sentry_sdk.set_tag("app", "sentineliq")
    
    logger.info(f"Sentry initialized for environment: {environment}")


def before_send(event, hint):
    """
    Filter and process events before sending to Sentry.
    Can be used to remove sensitive data or add additional context.
    
    Args:
        event: The event data
        hint: Additional information about the event
        
    Returns:
        Modified event or None to discard the event
    """
    # Get the exception if available
    exc_info = hint.get('exc_info')
    if exc_info:
        # Example: Add custom fingerprinting for certain exceptions
        pass
        
    # Filter out sensitive information if needed
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        # Remove authorization headers to avoid leaking credentials
        if 'Authorization' in headers:
            headers['Authorization'] = 'FILTERED'
        if 'Cookie' in headers:
            headers['Cookie'] = 'FILTERED'
    
    # Add environment info to help in debugging
    if os.environ.get('KUBERNETES_SERVICE_HOST'):
        event['tags']['deployment'] = 'kubernetes'
    
    return event


def before_breadcrumb(breadcrumb, hint):
    """
    Filter or modify breadcrumbs before they're added to the event.
    
    Args:
        breadcrumb: The breadcrumb data
        hint: Additional information about the breadcrumb
    
    Returns:
        Modified breadcrumb or None to discard
    """
    # Example: Filter out irrelevant queries to reduce noise
    if breadcrumb.get('category') == 'query':
        # Skip monitoring queries to reduce noise
        if 'SELECT 1' in breadcrumb.get('data', {}).get('query', ''):
            return None
    
    return breadcrumb


def capture_message(message, level="info", extra=None, tags=None):
    """
    Captures a user message with the given level.
    
    Args:
        message: The message to capture
        level: The level of the message (debug, info, warning, error, fatal)
        extra: Additional context data
        tags: Tags for filtering in Sentry
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
                
        sentry_sdk.capture_message(message, level=level)


def set_user(user_info):
    """
    Set the current user for Sentry events.
    
    Args:
        user_info: Dictionary containing user data
                  (id, email, username, etc.)
    """
    sentry_sdk.set_user(user_info)


def set_transaction(name):
    """
    Set the current transaction name.
    
    Args:
        name: The transaction name
    """
    sentry_sdk.set_tag("transaction", name)


def set_context(context_name, data):
    """
    Add additional context data to Sentry events.
    
    Args:
        context_name: The name of the context (e.g., 'request', 'server')
        data: The context data (dictionary)
    """
    sentry_sdk.set_context(context_name, data) 