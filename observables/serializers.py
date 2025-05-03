"""
This file is a redirection layer to maintain backward compatibility.
All new code should use the serializers from api/v1/observables/serializers.
"""
from api.v1.observables.serializers import (
    ObservableSerializer,
    ObservableDetailSerializer,
    ObservableCreateSerializer,
    ObservableHistorySerializer
)

__all__ = [
    'ObservableSerializer',
    'ObservableDetailSerializer',
    'ObservableCreateSerializer',
    'ObservableHistorySerializer',
] 