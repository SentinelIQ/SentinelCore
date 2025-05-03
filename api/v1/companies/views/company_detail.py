from rest_framework import status
from django.contrib.auth import get_user_model
from companies.models import Company
from django.db.models import Q
from api.core.viewsets import RetrieveModelMixin, ListModelMixin
from api.core.responses import error_response
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class CompanyDetailMixin(ListModelMixin, RetrieveModelMixin):
    """
    Mixin for company retrieve and list operations.
    """
    
    def get_queryset(self):
        """
        Filter companies based on user's permissions:
        - Superuser can see all companies
        - Company admin and analyst can see only their company
        
        Returns:
            Filtered queryset based on user permissions
        """
        user = self.request.user
        queryset = Company.objects.all()
        
        # Superuser can see all companies
        if user.is_superuser:
            return queryset
        
        # Regular user can only see their own company
        if hasattr(user, 'company') and user.company:
            return queryset.filter(id=user.company.id)
        
        # If no company, return empty queryset
        return Company.objects.none()

    def perform_update(self, serializer):
        """
        Update a company and log the action.
        
        Args:
            serializer: The validated serializer
            
        Returns:
            The updated company instance
        """
        user = self.request.user
        instance = serializer.save()
        logger.info(f"Company updated: {instance.name} by {user.username}")
        return instance
    
    def perform_destroy(self, instance):
        """
        Delete a company and log the action.
        
        Args:
            instance: The company instance to delete
            
        Raises:
            ValueError: If the company has associated users
        """
        name = instance.name
        user = self.request.user
        
        # Check if there are associated users
        if instance.users.exists():
            raise ValueError("Cannot delete a company that has associated users.")
        
        instance.delete()
        logger.info(f"Company deleted: {name} by {user.username}")
        return True 