from rest_framework import permissions
from sentinelvision.models import FeedModule

class CanExecuteFeedPermission(permissions.BasePermission):
    """
    Permission to check if a user can execute a feed.
    Rules:
    - If feed is linked to company: only users from that company can execute
    - If feed is not linked to company: only superusers can execute
    """
    message = "You don't have permission to execute this feed module."
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
            
        return True  # For list views, filtering will happen at object level
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can execute a specific feed.
        
        Args:
            request: The request
            view: The view
            obj: The feed module
            
        Returns:
            bool: True if user can execute feed
        """
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # For company-specific feeds, check if user belongs to that company
        if obj.company:
            return request.user.company == obj.company
        
        # For global feeds (no company), only superusers can execute
        return False
        
class IsSuperuserPermission(permissions.BasePermission):
    """
    Permission to check if a user is a superuser.
    """
    message = "Only superusers can perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser 