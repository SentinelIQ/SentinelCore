import logging
from django.db import models
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view

from wiki.models import KnowledgeCategory
from ..serializers import KnowledgeCategorySerializer
from api.core.viewsets import StandardViewSet

logger = logging.getLogger('api.wiki')


@extend_schema_view(
    list=extend_schema(tags=['Knowledge Base (Wiki)']),
    retrieve=extend_schema(tags=['Knowledge Base (Wiki)']),
    create=extend_schema(tags=['Knowledge Base (Wiki)']),
    update=extend_schema(tags=['Knowledge Base (Wiki)']),
    partial_update=extend_schema(tags=['Knowledge Base (Wiki)']),
    destroy=extend_schema(tags=['Knowledge Base (Wiki)'])
)
class KnowledgeCategoryViewSet(StandardViewSet):
    """
    API endpoint for managing knowledge categories.
    """
    serializer_class = KnowledgeCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'parent']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    entity_type = 'knowledge_category'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Category created successfully"
    success_message_update = "Category updated successfully"
    success_message_delete = "Category deleted successfully"
    
    def get_queryset(self):
        """
        Filter categories:
        - Superusers see all categories
        - Company users see global categories and their company's categories
        """
        user = self.request.user
        
        # Superusers can see all
        if user.is_superuser:
            return KnowledgeCategory.objects.all()
        
        # Company users see global categories and their company's categories
        if hasattr(user, 'company') and user.company:
            return KnowledgeCategory.objects.filter(
                models.Q(company__isnull=True) |  # Global
                models.Q(company=user.company)    # Company-specific
            )
        
        # Users without company only see global categories
        return KnowledgeCategory.objects.filter(company__isnull=True)
    
    def perform_create(self, serializer):
        """
        Set company for company users if not specified.
        """
        user = self.request.user
        company = serializer.validated_data.get('company')
        
        # If company not specified and user has company, use it
        if not company and not user.is_superuser and hasattr(user, 'company') and user.company:
            return serializer.save(company=user.company)
        else:
            return serializer.save() 