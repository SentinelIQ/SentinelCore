from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident', 'status', 'priority', 'due_date', 'assigned_to', 'company')
    list_filter = ('status', 'priority', 'company', 'due_date')
    search_fields = ('title', 'description', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'status', 'priority')
        }),
        ('Relationships', {
            'fields': ('incident', 'company', 'created_by', 'assigned_to')
        }),
        ('Timeline', {
            'fields': ('due_date', 'completion_date')
        }),
        ('Additional Information', {
            'fields': ('order', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """
        Filter tasks based on user's permissions:
        - Superuser can see all tasks
        - Company users can only see tasks from their company
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company) 