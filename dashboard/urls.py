from django.urls import path
from .views import (
    DashboardSummaryView, 
    IncidentTrendsView, 
    AlertSeverityView,
    DashboardPreferenceView,
    CustomMetricsView
)

app_name = 'dashboard'

urlpatterns = [
    # Dashboard summary with high-level stats
    path('summary/', DashboardSummaryView.as_view(), name='summary'),
    
    # Detailed metrics endpoints
    path('incidents/trends/', IncidentTrendsView.as_view(), name='incident-trends'),
    path('alerts/severity/', AlertSeverityView.as_view(), name='alert-severity'),
    
    # Custom metrics endpoint for dynamic queries
    path('custom/', CustomMetricsView.as_view(), name='custom-metrics'),
    
    # User dashboard preferences
    path('preferences/', DashboardPreferenceView.as_view(), name='preferences'),
] 