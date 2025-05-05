"""
Main Django app configuration for the API module.
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    Configuration for the API application.
    
    Defines initialization tasks when the API app is loaded.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """
        Initialize the API application.
        
        This method is called when Django starts, and is responsible for initializing
        various components such as signal handlers, scheduled tasks, etc.
        """
        # Register all models for audit logging
        from api.core.audit_registration import register_all_models
        register_all_models()
        
        # Import signals
        # This ensures that all signal handlers are properly connected
        import api.signals
