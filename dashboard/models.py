from django.db import models
from django.conf import settings
from companies.models import Company
from api.core.models import CoreModel

# Create your models here.

class DashboardPreference(CoreModel):
    """
    Stores user preferences for dashboard layouts and widgets.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_preferences')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='dashboard_preferences')
    
    # Layout settings stored as JSON
    layout = models.JSONField(default=dict, blank=True)
    
    # Widget preferences stored as JSON
    widget_preferences = models.JSONField(default=dict, blank=True)
    
    # Time range preferences (in days)
    default_time_range = models.PositiveIntegerField(default=7)
    
    class Meta:
        verbose_name = 'Dashboard Preference'
        verbose_name_plural = 'Dashboard Preferences'
        
    def __str__(self):
        return f"Dashboard preferences for {self.user.email}"
