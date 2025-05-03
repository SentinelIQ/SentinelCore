from django.contrib import admin
from .models import DashboardPreference

@admin.register(DashboardPreference)
class DashboardPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'default_time_range', 'created_at', 'updated_at')
    list_filter = ('company', 'default_time_range')
    search_fields = ('user__username', 'user__email', 'company__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'company', 'default_time_range')
        }),
        ('Advanced Settings', {
            'fields': ('layout', 'widget_preferences'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
