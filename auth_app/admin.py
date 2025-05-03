from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'company', 'is_staff')
    list_filter = ('role', 'company', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Company info'), {'fields': ('role', 'company')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only show users of the same company for non-superusers
        if not request.user.is_superuser and request.user.company:
            return qs.filter(company=request.user.company)
        return qs
    
    def get_readonly_fields(self, request, obj=None):
        # Company admins cannot change roles to superuser
        if not request.user.is_superuser:
            return ('is_superuser', 'is_staff', 'company', 'groups', 'user_permissions')
        return ()
    
    def save_model(self, request, obj, form, change):
        # Ensure company admins can only create users in their company
        if not request.user.is_superuser and request.user.company:
            obj.company = request.user.company
        super().save_model(request, obj, form, change)


admin.site.register(User, CustomUserAdmin)
