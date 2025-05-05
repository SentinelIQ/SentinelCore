"""
Core application configuration module.

This module configures the core API functionality including:
- Audit logging
- RBAC
- API response formatting
- Exception handling
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ApiCoreConfig(AppConfig):
    """Configuration for the API Core app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.core'
    verbose_name = "API Core"
    
    def ready(self):
        """
        Initialize app when Django is ready.
        
        This method:
        1. Registers models for audit logging
        2. Configures middleware
        3. Sets up signal handlers
        """
        # Import here to avoid AppRegistryNotReady exception
        from api.core.audit import register_models_for_audit
        
        # List of apps to audit
        AUDITED_APPS = [
            'auth_app',
            'companies',
            'alerts',
            'incidents',
            'observables',
            'tasks',
            'reporting',
            'wiki',
            'notifications',
            'dashboard',
            'sentinelvision',
            'mitre',
        ]
        
        # List of models to exclude from auditing
        EXCLUDED_MODELS = [
            'auth_app.token',
            'notifications.notificationlog',
            'wiki.pagerevision',
            'django.contrib.sessions.session',
            'django.contrib.admin.logentry',
            'django_celery_beat',
            'auditlog.logentry',
        ]
        
        # Register models for audit logging
        register_models_for_audit(
            app_list=AUDITED_APPS,
            exclude_models=EXCLUDED_MODELS
        )

        # Apply array field filter overrides globally
        from django_filters.rest_framework import filterset
        from django.contrib.postgres.fields import ArrayField
        from api.core.filters import ArrayFieldFilter
        
        # Register ArrayField filters
        filterset.FILTER_FOR_DBFIELD_DEFAULTS = {
            **filterset.FILTER_FOR_DBFIELD_DEFAULTS,
            ArrayField: {
                'filter_class': ArrayFieldFilter,
                'extra': lambda f: {
                    'lookup_expr': 'contains',
                }
            }
        }

        # Import signals to register them
        try:
            import api.core.signals
        except ImportError:
            logger.debug("No signals module found in api.core")

        # Initialize Sentry integration for API
        self._initialize_sentry()

    def _initialize_sentry(self):
        """
        Initialize Sentry integration for API monitoring and audit logging.
        """
        try:
            # Initialize API core monitoring
            from api.core.sentry import initialize_api_monitoring
            initialize_api_monitoring()
            
            # Initialize audit-sentry integration
            from api.core.audit_sentry import (
                initialize_audit_monitoring,
                monitor_security_events
            )
            
            # Set up audit monitoring
            initialize_audit_monitoring()
            
            # Monitor security-relevant events
            monitor_security_events()
            
            # Set up a periodic task to check for anomalies
            # This requires Celery to be properly configured
            try:
                from api.core.tasks import setup_anomaly_detection
                setup_anomaly_detection()
            except ImportError:
                logger.warning("Celery not available, skipping anomaly detection setup")
                
            logger.info("Sentry integration initialized for API monitoring and audit logging")
        except ImportError:
            logger.warning("Sentry SDK not available, API monitoring disabled")
        except Exception as e:
            logger.exception(f"Error initializing Sentry integration: {str(e)}") 