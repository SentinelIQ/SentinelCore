import logging
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.contrib.postgres.fields import ArrayField
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample

from wiki.models import KnowledgeArticle
from ..serializers import KnowledgeArticleSerializer
from ..permissions import CanAccessArticle, CanManageArticle
from api.core.responses import success_response, error_response
from api.core.viewsets import StandardViewSet
from api.core.filters import get_array_field_filter_overrides
from api.core.pagination import StandardResultsSetPagination
import markdown2

logger = logging.getLogger('api.wiki')


# Custom filterset for KnowledgeArticle to handle ArrayField (tags)
class KnowledgeArticleFilterSet(FilterSet):
    class Meta:
        model = KnowledgeArticle
        fields = ['company', 'category', 'visibility', 'author', 'tags', 'is_reviewed']
        filter_overrides = get_array_field_filter_overrides()


@extend_schema_view(
    list=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="List knowledge articles",
        description=(
            "Retrieves a list of knowledge articles (wiki pages) with filtering capabilities. "
            "The knowledge base is a critical component of the SOAR platform that stores security "
            "playbooks, standard operating procedures, and technical documentation. This endpoint "
            "supports multi-tenant isolation and visibility control, ensuring users only see "
            "appropriate content for their organization. Articles can be filtered by category, "
            "tags, and visibility settings. The content supports Markdown formatting for rich "
            "documentation including code snippets, tables, and procedures."
        ),
        responses={
            200: OpenApiResponse(
                description="Articles retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="article_list",
                        summary="Knowledge article list",
                        description="Example showing a paginated list of articles",
                        value={
                            "count": 15,
                            "next": "https://api.example.com/api/v1/wiki/articles/?page=2",
                            "previous": None,
                            "results": [
                                {
                                    "id": "f3221f77-f3f1-458d-98a1-26a9d8d33b8a",
                                    "title": "Phishing Incident Response Playbook",
                                    "slug": "phishing-incident-response-playbook",
                                    "visibility": "private",
                                    "category": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                                    "category_name": "Incident Response",
                                    "tags": ["phishing", "playbook", "email", "incident-response"],
                                    "author": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                                    "author_name": "John Smith",
                                    "created_at": "2023-05-15T09:30:22.123456Z",
                                    "updated_at": "2023-07-10T14:15:32.789012Z",
                                    "is_reviewed": True
                                }
                            ]
                        }
                    )
                ]
            )
        }
    ),
    retrieve=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Retrieve knowledge article",
        description=(
            "Retrieves a detailed knowledge article by its slug identifier. Knowledge articles "
            "contain essential security documentation such as playbooks, procedures, and technical "
            "references. The content is returned in both Markdown format and as rendered HTML. "
            "This endpoint is essential for security analysts who need to follow documented "
            "procedures during incident response. Articles can include formatted content with "
            "checklists, code blocks, diagrams, and procedural steps."
        ),
        responses={
            200: OpenApiResponse(
                description="Article retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="article_detail",
                        summary="Knowledge article detail",
                        description="Example showing a detailed knowledge article",
                        value={
                            "id": "f3221f77-f3f1-458d-98a1-26a9d8d33b8a",
                            "title": "Phishing Incident Response Playbook",
                            "slug": "phishing-incident-response-playbook",
                            "content": "# Phishing Incident Response Playbook\n\n## Overview\nThis playbook outlines the steps...",
                            "html_content": "<h1>Phishing Incident Response Playbook</h1><h2>Overview</h2><p>This playbook outlines the steps...</p>",
                            "visibility": "private",
                            "category": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                            "category_name": "Incident Response",
                            "tags": ["phishing", "playbook", "email", "incident-response"],
                            "company": "7c637454-d1e9-4763-9aa8-c1050e07ad10",
                            "author": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                            "author_name": "John Smith",
                            "created_at": "2023-05-15T09:30:22.123456Z",
                            "updated_at": "2023-07-10T14:15:32.789012Z",
                            "published_at": "2023-05-15T10:00:00.000000Z",
                            "expires_at": None,
                            "is_reviewed": True,
                            "version": 2
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Article not found error",
                examples=[
                    OpenApiExample(
                        name="article_not_found",
                        summary="Article not found error",
                        description="Example of response when the specified article doesn't exist",
                        value={
                            "status": "error",
                            "message": "Knowledge article not found",
                            "data": None
                        }
                    )
                ]
            )
        }
    ),
    create=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Create knowledge article",
        description=(
            "Creates a new knowledge article in the security wiki. Knowledge articles store "
            "important security documentation such as incident response playbooks, standard "
            "operating procedures, and technical reference materials. This endpoint supports "
            "Markdown formatting for rich content including code snippets, tables, and checklists. "
            "The article's visibility can be set to control access across the organization. Tags "
            "and categories help with organization and searchability of the knowledge base."
        ),
        responses={
            201: OpenApiResponse(
                description="Article created successfully",
                examples=[
                    OpenApiExample(
                        name="article_created",
                        summary="Knowledge article created",
                        description="Example of response when an article is successfully created",
                        value={
                            "status": "success",
                            "message": "Article created successfully",
                            "data": {
                                "id": "f3221f77-f3f1-458d-98a1-26a9d8d33b8a",
                                "title": "Ransomware Containment Procedure",
                                "slug": "ransomware-containment-procedure",
                                "visibility": "private",
                                "category": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                                "author": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                                "created_at": "2023-07-20T11:25:32.123456Z"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid article data",
                examples=[
                    OpenApiExample(
                        name="validation_error",
                        summary="Validation error",
                        description="Example of response when the article data is invalid",
                        value={
                            "status": "error",
                            "message": "Invalid article data",
                            "errors": {
                                "title": ["This field is required."],
                                "visibility": ["Public articles cannot be associated with a company."]
                            }
                        }
                    )
                ]
            )
        }
    ),
    update=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Update knowledge article",
        description=(
            "Updates an existing knowledge article in the security wiki. This endpoint allows "
            "security teams to maintain up-to-date documentation as procedures and playbooks "
            "evolve. When articles are updated, the version number is automatically incremented "
            "to track changes over time. Updated articles can be marked for review to ensure "
            "quality control in the knowledge base."
        )
    ),
    partial_update=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Partially update knowledge article",
        description=(
            "Partially updates an existing knowledge article, modifying only the specified fields. "
            "This is useful for making small changes to content, updating tags, or changing the "
            "article's category without resubmitting the entire article content."
        )
    ),
    destroy=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Delete knowledge article",
        description=(
            "Deletes a knowledge article from the security wiki. This operation permanently "
            "removes the article and cannot be undone. Typically, articles should be archived "
            "rather than deleted to maintain the knowledge history of the security organization."
        )
    ),
    render_markdown=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Render markdown content as HTML",
        description=(
            "Converts the article's markdown content to HTML for rendering in web interfaces. "
            "This endpoint is useful for client applications that need to display formatted "
            "content but don't have their own markdown rendering capabilities. The HTML output "
            "includes proper formatting for code blocks, tables, headers, and other markdown "
            "elements essential for security documentation."
        ),
        responses={
            200: OpenApiResponse(
                description="Markdown rendered successfully",
                examples=[
                    OpenApiExample(
                        name="rendered_markdown",
                        summary="Rendered markdown content",
                        description="Example showing markdown content rendered as HTML",
                        value={
                            "status": "success",
                            "message": "Markdown rendered successfully",
                            "data": {
                                "html_content": "<h1>Phishing Incident Response Playbook</h1><h2>Overview</h2><p>This playbook outlines the steps...</p>"
                            }
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Rendering error",
                examples=[
                    OpenApiExample(
                        name="rendering_error",
                        summary="Markdown rendering error",
                        description="Example of response when there's an error rendering the markdown",
                        value={
                            "status": "error",
                            "message": "Error rendering markdown content",
                            "data": None
                        }
                    )
                ]
            )
        }
    )
)
class KnowledgeArticleViewSet(StandardViewSet):
    """
    ViewSet for Knowledge Articles that represent the internal wiki.
    
    Knowledge articles store important security documentation such as 
    playbooks, procedures, and reference materials.
    """
    serializer_class = KnowledgeArticleSerializer
    lookup_field = 'slug'
    pagination_class = StandardResultsSetPagination
    permission_classes = [CanAccessArticle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = KnowledgeArticleFilterSet
    search_fields = ['title', 'content', 'tags']
    ordering_fields = ['title', 'created_at', 'updated_at', 'is_reviewed']
    ordering = ['title']
    entity_type = 'wiki'  # Define entity type for RBAC
    
    # Define visibility constants for easier reference
    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_PRIVATE = 'private'
    
    # Success messages for standardized responses
    success_message_create = "Article created successfully"
    success_message_update = "Article updated successfully"
    success_message_delete = "Article deleted successfully"
    
    def get_permissions(self):
        """
        Override to add object permissions for detail views.
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated]  # Basic auth check for creation
        else:
            permission_classes = self.permission_classes
            
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Return articles based on visibility and company.
        
        - Public articles are visible to all
        - Private articles are only visible to users in the same company
        """
        # Handle schema generation
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return KnowledgeArticle.objects.none()
            
        user = self.request.user
        
        # Base queryset starts with all public articles
        queryset = KnowledgeArticle.objects.filter(visibility=self.VISIBILITY_PUBLIC)
        
        # If user is authenticated, add private articles for their company
        if user.is_authenticated and hasattr(user, 'company') and user.company:
            # Combine public articles with private articles for user's company
            queryset = queryset | KnowledgeArticle.objects.filter(
                visibility=self.VISIBILITY_PRIVATE,
                company=user.company
            )
        
        # If user is superuser, show all articles
        if user.is_superuser:
            queryset = KnowledgeArticle.objects.all()
            
        return queryset.distinct()
    
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