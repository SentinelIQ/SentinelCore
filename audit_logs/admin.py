from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Django Admin configuration for AuditLog model.
    """
    list_display = (
        'timestamp', 'action', 'entity_type', 'entity_name', 
        'username', 'company_name', 'response_status'
    )
    list_filter = (
        'action', 'entity_type', 'timestamp',
        'company_name'
    )
    search_fields = (
        'username', 'entity_name', 'company_name', 'ip_address',
        'entity_id'
    )
    readonly_fields = (
        'id', 'user', 'username', 'ip_address', 'user_agent',
        'action', 'action_details', 'entity_type', 'entity_id',
        'entity_name', 'company_id', 'company_name', 'request_method',
        'request_path', 'request_data', 'response_status',
        'additional_data', 'timestamp'
    )
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Disable manual creation of audit logs"""
        return False
        
    def has_change_permission(self, request, obj=None):
        """Audit logs should never be modified"""
        return False 