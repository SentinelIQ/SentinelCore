from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.v1.mitre.views import (
    MitreTacticView,
    MitreTechniqueView,
    MitreMitigationView,
    MitreRelationshipView,
    AlertMitreMappingView,
    IncidentMitreMappingView,
    ObservableMitreMappingView
)

router = DefaultRouter()
router.register('tactics', MitreTacticView, basename='mitre-tactics')
router.register('techniques', MitreTechniqueView, basename='mitre-techniques')
router.register('mitigations', MitreMitigationView, basename='mitre-mitigations')
router.register('relationships', MitreRelationshipView, basename='mitre-relationships')
router.register('alert-mappings', AlertMitreMappingView, basename='mitre-alert-mappings')
router.register('incident-mappings', IncidentMitreMappingView, basename='mitre-incident-mappings')
router.register('observable-mappings', ObservableMitreMappingView, basename='mitre-observable-mappings')

urlpatterns = [
    path('', include(router.urls)),
] 