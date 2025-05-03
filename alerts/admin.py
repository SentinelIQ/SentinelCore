from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'status', 'company', 'created_by', 'created_at', 'artifact_count')
    list_filter = ('severity', 'status', 'company', 'created_at')
    search_fields = ('title', 'description', 'source')
    readonly_fields = ('id', 'created_at', 'updated_at', 'artifact_count')
    filter_horizontal = ('observables',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'severity', 'source', 'status')
        }),
        ('Relationships', {
            'fields': ('company', 'created_by')
        }),
        ('MITRE ATT&CK', {
            'fields': ('primary_technique', 'sub_technique'),
            'description': 'MITRE ATT&CK techniques and sub-techniques associated with this alert'
        }),
        ('Observables', {
            'fields': ('observables', 'observable_data', 'artifact_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def get_queryset(self, request):
        """
        Add prefetch_related for observables to improve admin performance.
        """
        return super().get_queryset(request).prefetch_related('observables') 