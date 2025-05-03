"""
SentinelIQ - Enterprise-grade security platform.
"""

# Import Celery app
from __future__ import absolute_import, unicode_literals
from .celery import app as celery_app

# Initialize Sentry
try:
    from .sentry import setup_sentry
    setup_sentry()
except ImportError:
    # Log this failure gracefully in production
    import logging
    logging.getLogger('sentineliq').warning("Could not initialize Sentry. Continuing without error monitoring.")

__all__ = ('celery_app',)
