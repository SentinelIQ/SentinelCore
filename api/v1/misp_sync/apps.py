from django.apps import AppConfig


class MispSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api.v1.misp_sync"
    label = "misp_sync"
    verbose_name = "MISP Sync"

    def ready(self):
        """
        Initialize the app when Django starts.
        Import signals and register models for audit logging.
        """
        # Import signals
        import api.v1.misp_sync.signals
        
        # Register models for audit logging
        from auditlog.registry import auditlog
        from .models import MISPServer, MISPEvent, MISPAttribute
        
        # Register models for audit logging
        auditlog.register(MISPServer)
        auditlog.register(MISPEvent)
        auditlog.register(MISPAttribute)
