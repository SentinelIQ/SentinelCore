import logging
from django.db import models
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample

from wiki.models import KnowledgeCategory
from ..serializers import KnowledgeCategorySerializer
from api.core.viewsets import StandardViewSet

logger = logging.getLogger('api.wiki')


@extend_schema_view(
    list=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="List knowledge categories",
        description=(
            "Retrieves a list of knowledge base categories used for organizing security documentation. "
            "Categories provide a hierarchical structure for organizing playbooks, procedures, and "
            "technical documentation in the security knowledge base. This endpoint supports multi-tenant "
            "isolation, ensuring users only see appropriate categories for their organization. Global "
            "categories are visible to all companies, while company-specific categories are only visible "
            "to users of that company. Categories can be nested to create a hierarchical structure."
        ),
        responses={
            200: OpenApiResponse(
                description="Categories retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="category_list",
                        summary="Knowledge category list",
                        description="Example showing a list of knowledge categories",
                        value={
                            "count": 8,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "id": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                                    "name": "Incident Response",
                                    "slug": "incident-response",
                                    "description": "Playbooks and procedures for responding to security incidents",
                                    "parent": None,
                                    "company": "7c637454-d1e9-4763-9aa8-c1050e07ad10",
                                    "created_at": "2023-01-10T09:30:22.123456Z",
                                    "updated_at": "2023-01-10T09:30:22.123456Z"
                                },
                                {
                                    "id": "b2840a9b-8ecb-558a-0f7d-1c46e2f9cd31",
                                    "name": "Phishing Response",
                                    "slug": "phishing-response",
                                    "description": "Procedures specific to phishing incident response",
                                    "parent": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                                    "company": "7c637454-d1e9-4763-9aa8-c1050e07ad10",
                                    "created_at": "2023-01-15T11:20:45.789012Z",
                                    "updated_at": "2023-01-15T11:20:45.789012Z"
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
        summary="Retrieve knowledge category",
        description=(
            "Retrieves detailed information about a specific knowledge category by its ID. "
            "Categories are used to organize security documentation in a hierarchical structure. "
            "This endpoint returns the category's details including name, description, and parent "
            "category if it exists. This information is used to build navigation structures for "
            "knowledge base interfaces and to organize related security documentation."
        ),
        responses={
            200: OpenApiResponse(
                description="Category retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="category_detail",
                        summary="Knowledge category detail",
                        description="Example showing a detailed knowledge category",
                        value={
                            "id": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                            "name": "Incident Response",
                            "slug": "incident-response",
                            "description": "Playbooks and procedures for responding to security incidents",
                            "parent": None,
                            "company": "7c637454-d1e9-4763-9aa8-c1050e07ad10",
                            "created_at": "2023-01-10T09:30:22.123456Z",
                            "updated_at": "2023-01-10T09:30:22.123456Z"
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Category not found",
                examples=[
                    OpenApiExample(
                        name="category_not_found",
                        summary="Category not found error",
                        description="Example of response when the specified category doesn't exist",
                        value={
                            "status": "error",
                            "message": "Knowledge category not found",
                            "data": None
                        }
                    )
                ]
            )
        }
    ),
    create=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Create knowledge category",
        description=(
            "Creates a new knowledge category for organizing security documentation. Categories "
            "provide a hierarchical structure for the knowledge base, helping security teams "
            "organize their playbooks, procedures, and technical documentation. Categories can "
            "be company-specific or global (visible to all companies). They can also be nested "
            "by specifying a parent category, allowing for a tree-like organization of content."
        ),
        responses={
            201: OpenApiResponse(
                description="Category created successfully",
                examples=[
                    OpenApiExample(
                        name="category_created",
                        summary="Knowledge category created",
                        description="Example of response when a category is successfully created",
                        value={
                            "status": "success",
                            "message": "Category created successfully",
                            "data": {
                                "id": "c3951b8c-9fdc-669b-1a8e-2d57f3a0de42",
                                "name": "Ransomware Response",
                                "slug": "ransomware-response",
                                "description": "Procedures for responding to ransomware incidents",
                                "parent": "a1739d9a-7db9-447a-9e6c-9b35d1f8be20",
                                "company": "7c637454-d1e9-4763-9aa8-c1050e07ad10"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid category data",
                examples=[
                    OpenApiExample(
                        name="validation_error",
                        summary="Validation error",
                        description="Example of response when the category data is invalid",
                        value={
                            "status": "error",
                            "message": "Invalid category data",
                            "errors": {
                                "name": ["This field is required."],
                                "parent": ["Invalid parent category."]
                            }
                        }
                    )
                ]
            )
        }
    ),
    update=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Update knowledge category",
        description=(
            "Updates an existing knowledge category with new values. This endpoint is used to "
            "modify category details such as name, description, or parent category. Updating "
            "a category affects the organization of all articles within that category."
        )
    ),
    partial_update=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Partially update knowledge category",
        description=(
            "Partially updates an existing knowledge category, modifying only the specified fields. "
            "This is useful for making small changes to category details without resubmitting all "
            "the category information."
        )
    ),
    destroy=extend_schema(
        tags=['Knowledge Base (Wiki)'],
        summary="Delete knowledge category",
        description=(
            "Deletes a knowledge category from the system. This operation should be used with caution "
            "as it may affect articles assigned to this category. If articles are assigned to the category "
            "being deleted, consider reassigning them first or updating the API to handle orphaned articles."
        ),
        responses={
            204: OpenApiResponse(
                description="Category deleted successfully"
            ),
            400: OpenApiResponse(
                description="Cannot delete category with articles",
                examples=[
                    OpenApiExample(
                        name="delete_error",
                        summary="Delete error",
                        description="Example of response when the category cannot be deleted",
                        value={
                            "status": "error",
                            "message": "Cannot delete category with existing articles. Reassign articles first.",
                            "data": None
                        }
                    )
                ]
            )
        }
    )
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