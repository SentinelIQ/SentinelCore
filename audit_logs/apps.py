from django.apps import AppConfig


class AuditLogsConfig(AppConfig):
    """
    Configuration for the audit_logs app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit_logs'
    verbose_name = 'Audit Logs' 