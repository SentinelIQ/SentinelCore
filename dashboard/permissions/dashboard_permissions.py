from rest_framework import permissions
from auth_app.permission_matrix import has_permission


class CanViewDashboard(permissions.BasePermission):
    """
    Permission to check if a user can view dashboards.
    """
    def has_permission(self, request, view):
        return has_permission(request.user.role, 'view_dashboard') 