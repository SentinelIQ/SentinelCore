"""
DEPRECATED: This file is kept for backward compatibility.
All new code should use the views from api/v1/observables/views.
"""
from api.v1.observables.views import ObservableViewSet

# This export maintains backwards compatibility
__all__ = ['ObservableViewSet'] 