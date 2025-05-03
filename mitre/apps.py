from django.apps import AppConfig


class MitreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mitre"
    verbose_name = "MITRE ATT&CK Framework"

    def ready(self):
        """
        Register any signals or other initialization here
        """
        pass
