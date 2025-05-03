"""
This file is a redirection layer to maintain backward compatibility.
All new code should use the views from api/v1/mitre/views.
"""
from api.v1.mitre.views import (
    MitreTacticView,
    MitreTechniqueView,
    MitreMitigationView,
    MitreRelationshipView,
    AlertMitreMappingView,
    IncidentMitreMappingView,
    ObservableMitreMappingView
)

__all__ = [
    'MitreTacticView',
    'MitreTechniqueView',
    'MitreMitigationView',
    'MitreRelationshipView',
    'AlertMitreMappingView',
    'IncidentMitreMappingView',
    'ObservableMitreMappingView',
]
