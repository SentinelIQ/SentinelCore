from django.contrib import admin
from api.v1.misp_sync.models import MISPServer, MISPEvent, MISPAttribute


@admin.register(MISPServer)
class MISPServerAdmin(admin.ModelAdmin):
    """Admin view for MISP Server configurations"""
    list_display = ('name', 'url', 'company', 'is_active', 'last_sync', 'created_at', 'updated_at')
    list_filter = ('is_active', 'company', 'created_at')
    search_fields = ('name', 'url', 'description', 'company__name')
    readonly_fields = ('created_at', 'updated_at', 'last_sync')
    fieldsets = (
        ('Server Information', {
            'fields': ('name', 'url', 'description', 'company', 'created_by')
        }),
        ('Authentication', {
            'fields': ('api_key', 'verify_ssl')
        }),
        ('Synchronization Settings', {
            'fields': ('is_active', 'sync_interval_hours', 'last_sync')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MISPEvent)
class MISPEventAdmin(admin.ModelAdmin):
    """Admin view for MISP Events"""
    list_display = ('info', 'misp_id', 'company', 'org_name', 'date', 'threat_level_id', 'published', 'timestamp')
    list_filter = ('company', 'misp_server', 'threat_level_id', 'published', 'date')
    search_fields = ('info', 'org_name', 'orgc_name', 'tags')
    readonly_fields = ('created_at', 'updated_at', 'uuid', 'misp_uuid', 'timestamp')
    fieldsets = (
        ('Event Information', {
            'fields': ('info', 'misp_id', 'misp_uuid', 'uuid', 'date', 'org_name', 'orgc_name', 'tags')
        }),
        ('MISP Settings', {
            'fields': ('threat_level_id', 'analysis', 'distribution', 'published')
        }),
        ('Relationships', {
            'fields': ('company', 'misp_server')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'timestamp')
        }),
    )


@admin.register(MISPAttribute)
class MISPAttributeAdmin(admin.ModelAdmin):
    """Admin view for MISP Attributes"""
    list_display = ('type', 'category', 'value', 'event', 'to_ids', 'timestamp')
    list_filter = ('type', 'category', 'to_ids', 'event__company')
    search_fields = ('value', 'comment', 'tags', 'event__info')
    readonly_fields = ('created_at', 'updated_at', 'uuid', 'misp_uuid', 'timestamp')
    fieldsets = (
        ('Attribute Information', {
            'fields': ('type', 'category', 'value', 'comment', 'tags')
        }),
        ('MISP Settings', {
            'fields': ('misp_id', 'misp_uuid', 'uuid', 'to_ids', 'distribution')
        }),
        ('Relationships', {
            'fields': ('event',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'timestamp')
        }),
    )
