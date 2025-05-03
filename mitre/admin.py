from django.contrib import admin
from .models import (
    MitreTactic, 
    MitreTechnique, 
    MitreMitigation, 
    MitreRelationship,
    MitreMitigationMapping,
    AlertMitreMapping,
    IncidentMitreMapping,
    ObservableMitreMapping
)


@admin.register(MitreTactic)
class MitreTacticAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'name')
    search_fields = ('external_id', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MitreTechnique)
class MitreTechniqueAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'name', 'is_subtechnique', 'get_tactics')
    search_fields = ('external_id', 'name', 'description')
    list_filter = ('is_subtechnique', 'tactics', 'platforms')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tactics',)
    
    def get_tactics(self, obj):
        return ', '.join([tactic.name for tactic in obj.tactics.all()])
    get_tactics.short_description = 'Tactics'


@admin.register(MitreMitigation)
class MitreMitigationAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'name')
    search_fields = ('external_id', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MitreRelationship)
class MitreRelationshipAdmin(admin.ModelAdmin):
    list_display = ('source_id', 'relationship_type', 'target_id')
    search_fields = ('source_id', 'target_id', 'relationship_type')
    list_filter = ('relationship_type',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MitreMitigationMapping)
class MitreMitigationMappingAdmin(admin.ModelAdmin):
    list_display = ('mitigation', 'technique')
    search_fields = ('mitigation__name', 'technique__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AlertMitreMapping)
class AlertMitreMappingAdmin(admin.ModelAdmin):
    list_display = ('alert', 'technique', 'confidence', 'auto_detected')
    search_fields = ('alert__title', 'technique__name')
    list_filter = ('auto_detected',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(IncidentMitreMapping)
class IncidentMitreMappingAdmin(admin.ModelAdmin):
    list_display = ('incident', 'technique', 'confidence')
    search_fields = ('incident__title', 'technique__name', 'notes')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ObservableMitreMapping)
class ObservableMitreMappingAdmin(admin.ModelAdmin):
    list_display = ('observable', 'technique', 'confidence', 'auto_detected')
    search_fields = ('observable__value', 'technique__name')
    list_filter = ('auto_detected',)
    readonly_fields = ('created_at', 'updated_at')
