from django.apps import AppConfig


class IncidentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'incidents'
    verbose_name = 'Incidents'
    
    def ready(self):
        """
        Register signals when the app is ready.
        """
        import incidents.signals 