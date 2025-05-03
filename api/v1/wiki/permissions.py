from rest_framework import permissions
from api.core.rbac import HasEntityPermission
from wiki.models import KnowledgeArticle


class CanAccessArticle(HasEntityPermission):
    """
    Permission class that checks if a user can access an article based on:
    1. Public articles are accessible to all authenticated users
    2. Private articles are only accessible to users in the same company
    3. Superusers can access all articles
    """
    entity_type = 'knowledge_article'
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Superusers can access all
        if user.is_superuser:
            return True
        
        # Check visibility
        if obj.visibility == KnowledgeArticle.Visibility.PUBLIC:
            return True
        
        # For private articles, check company
        if obj.visibility == KnowledgeArticle.Visibility.PRIVATE:
            return hasattr(user, 'company') and user.company == obj.company
        
        return False


class CanManageArticle(HasEntityPermission):
    """
    Permission class that checks if a user can manage (edit/delete) an article.
    1. Superusers can manage all articles
    2. Company admins can manage their company's articles
    3. Article authors can manage their own articles
    """
    entity_type = 'knowledge_article'
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Superusers can manage all
        if user.is_superuser:
            return True
        
        # Check if user is the author
        if obj.author == user:
            return True
        
        # Company admins can manage their company's articles
        if (hasattr(user, 'is_admin_company') and user.is_admin_company and 
            hasattr(user, 'company') and obj.company and user.company == obj.company):
            return True
        
        return False 