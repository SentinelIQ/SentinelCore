"""
Celery signal handlers for SentinelIQ.
This module contains signal handlers for Celery to ensure proper monitoring with Sentry.
"""

from celery import signals
import logging
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

logger = logging.getLogger('celery')


@signals.celeryd_init.connect
def init_sentry_worker(**kwargs):
    """
    Initialize Sentry when Celery worker starts.
    This ensures proper monitoring of Celery worker tasks.
    """
    from .sentry import setup_sentry
    logger.info("Initializing Sentry for Celery worker...")
    setup_sentry()
    logger.info("Sentry initialized for Celery worker")


@signals.beat_init.connect
def init_sentry_beat(**kwargs):
    """
    Initialize Sentry when Celery beat starts.
    This ensures proper monitoring of scheduled tasks.
    """
    logger.info("Initializing Sentry for Celery Beat...")
    
    # Import locally to avoid circular imports
    from django.conf import settings
    import os
    
    # Get environment and release info
    environment = getattr(settings, 'ENVIRONMENT', 'development')
    dsn = os.environ.get('SENTRY_DSN')
    
    if not dsn:
        logger.warning("Sentry DSN not found. Skipping Sentry initialization for Beat.")
        return
    
    # Initialize Sentry specifically for Beat
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            CeleryIntegration(
                monitor_beat_tasks=True,
                exclude_beat_tasks=[
                    "healthcheck",
                    "cleanup_.*",
                    "celery.backend_cleanup",
                    "django_celery_beat.tasks.delete_expired_task_states",
                ]
            )
        ],
        environment=environment,
        # Use the same release as the main application if available
        release=os.environ.get('SENTRY_RELEASE'),
    )
    
    # Add beat-specific context
    sentry_sdk.set_tag("service", "celery-beat")
    logger.info(f"Sentry initialized for Celery Beat in {environment} environment") 