import logging
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.contrib.postgres.fields import ArrayField
from drf_spectacular.utils import extend_schema, extend_schema_view

from wiki.models import KnowledgeArticle
from ..serializers import KnowledgeArticleSerializer
from ..permissions import CanAccessArticle, CanManageArticle
from api.core.responses import success_response, error_response
from api.core.viewsets import StandardViewSet
from api.core.filters import get_array_field_filter_overrides
import markdown2

logger = logging.getLogger('api.wiki')


# Custom filterset for KnowledgeArticle to handle ArrayField (tags)
class KnowledgeArticleFilterSet(FilterSet):
    class Meta:
        model = KnowledgeArticle
        fields = ['company', 'category', 'visibility', 'author', 'tags', 'is_reviewed']
        filter_overrides = get_array_field_filter_overrides()


@extend_schema_view(
    list=extend_schema(tags=['Wiki Articles']),
    retrieve=extend_schema(tags=['Wiki Articles']),
    create=extend_schema(tags=['Wiki Articles']),
    update=extend_schema(tags=['Wiki Articles']),
    partial_update=extend_schema(tags=['Wiki Articles']),
    destroy=extend_schema(tags=['Wiki Articles']),
    render_markdown=extend_schema(tags=['Wiki Articles']),
)
class KnowledgeArticleViewSet(StandardViewSet):
    """
    API endpoint for managing knowledge articles (the wiki).
    """
    serializer_class = KnowledgeArticleSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = KnowledgeArticleFilterSet
    search_fields = ['title', 'slug', 'content', 'tags']
    ordering_fields = ['title', 'created_at', 'updated_at', 'published_at']
    ordering = ['-updated_at']
    entity_type = 'knowledge_article'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Article created successfully"
    success_message_update = "Article updated successfully"
    success_message_delete = "Article deleted successfully"
    
    def get_permissions(self):
        """
        - List/retrieve: CanAccessArticle
        - Create: IsAuthenticated
        - Update/delete: CanManageArticle
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [CanManageArticle()]
        elif self.action in ['retrieve', 'list']:
            return [IsAuthenticated(), CanAccessArticle()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Filter articles based on user's company and article visibility:
        - Superusers see all articles
        - Company users see public articles and their company's private articles
        """
        user = self.request.user
        
        # Superusers can see all
        if user.is_superuser:
            return KnowledgeArticle.objects.all()
        
        # Company users see public articles and their company's private articles
        if hasattr(user, 'company') and user.company:
            return KnowledgeArticle.objects.filter(
                models.Q(visibility=KnowledgeArticle.Visibility.PUBLIC) |  # Public
                models.Q(visibility=KnowledgeArticle.Visibility.PRIVATE, company=user.company)  # Private for company
            ).filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())  # Not expired
            ).filter(
                published_at__lte=timezone.now()  # Already published
            )
        
        # Users without company only see public articles
        return KnowledgeArticle.objects.filter(
            visibility=KnowledgeArticle.Visibility.PUBLIC,
            published_at__lte=timezone.now()
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )
    
    def perform_create(self, serializer):
        """
        Set author and company when creating an article.
        """
        user = self.request.user
        company = serializer.validated_data.get('company')
        visibility = serializer.validated_data.get('visibility')
        
        with transaction.atomic():
            # For private articles, ensure company is set
            if visibility == KnowledgeArticle.Visibility.PRIVATE and not company:
                if hasattr(user, 'company') and user.company:
                    return serializer.save(author=user, company=user.company)
                else:
                    raise ValidationError({
                        'company': 'Private articles must be associated with a company.'
                    })
            else:
                return serializer.save(author=user)
    
    @extend_schema(
        summary="Render markdown content as HTML",
        description="Converts the article's markdown content to HTML for rendering",
        responses={
            200: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}, "data": {"type": "object", "properties": {"html_content": {"type": "string"}}}}},
            500: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}
        }
    )
    @action(detail=True, methods=['get'], url_path='render')
    def render_markdown(self, request, slug=None):
        """
        Renders the article's markdown content as HTML.
        """
        article = self.get_object()
        
        try:
            html_content = markdown2.markdown(
                article.content,
                extras=["tables", "code-friendly", "fenced-code-blocks"]
            )
            
            return success_response(
                data={'html_content': html_content},
                message="Markdown rendered successfully"
            )
        except Exception as e:
            logger.error(f"Error rendering markdown for article {article.id}: {str(e)}", exc_info=True)
            return error_response(
                message="Error rendering markdown content",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 