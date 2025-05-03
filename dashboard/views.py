"""
This file is a redirection layer to maintain backward compatibility.
All new code should use the views from dashboard/views.
"""
from dashboard.views import (
    DashboardSummaryView,
    IncidentTrendsView,
    AlertSeverityView,
    DashboardPreferenceView,
    CustomMetricsView
)

__all__ = [
    'DashboardSummaryView',
    'IncidentTrendsView',
    'AlertSeverityView',
    'DashboardPreferenceView',
    'CustomMetricsView'
]
