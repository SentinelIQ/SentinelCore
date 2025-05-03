from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only superusers can see all companies
        if not request.user.is_superuser and request.user.company:
            return qs.filter(id=request.user.company.id)
        return qs
    
    def has_add_permission(self, request):
        # Only superusers can add companies
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete companies
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        # Superusers can change any company, company admins can only view their own
        if request.user.is_superuser:
            return True
        if obj and request.user.is_admin_company and request.user.company == obj:
            return True
        return False
