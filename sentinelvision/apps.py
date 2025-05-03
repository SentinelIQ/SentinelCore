from django.apps import AppConfig


class SentinelvisionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sentinelvision"
    verbose_name = "Sentinel Vision"

    def ready(self):
        """
        Perform app initialization when Django starts.
        """
        # Import signals to ensure they are registered
        import sentinelvision.signals
        
        # Import and run feed discovery to ensure all feeds are registered
        from sentinelvision.feeds import discover_feeds
        discover_feeds()
