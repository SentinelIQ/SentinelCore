from django.apps import AppConfig


class ApiCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.core'
    
    def ready(self):
        """
        Override ready method to register custom components and apply global settings.
        """
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