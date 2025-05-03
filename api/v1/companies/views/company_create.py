from rest_framework import status
from django.db import transaction
from rest_framework.response import Response
from companies.models import Company
from api.core.viewsets import CreateModelMixin
from api.core.responses import error_response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from ..serializers import CompanyCreateSerializer
import logging

logger = logging.getLogger(__name__)


class CompanyCreateMixin(CreateModelMixin):
    """
    Mixin for company creation operations.
    Enforces strict rules for company creation:
    - Only adminsentinel (superuser) can create companies
    - Each company must have at least one admin_company user
    """
    success_message_create = "Company created successfully"
    
    @extend_schema(
        summary="Create a new company with admin",
        description="""
        Creates a new company in the system along with an admin user.
        
        **Permissions:**
        - Only superusers can create companies
        
        **Required data:**
        - Company name
        - Admin user information (email, password, etc.)
        """,
        request=CompanyCreateSerializer,
        responses={
            201: CompanyCreateSerializer,
            400: {"description": "Invalid input data"},
            403: {"description": "Not authorized to create companies"}
        },
        examples=[
            OpenApiExample(
                "Company Creation Example",
                value={
                    "name": "Nome da Empresa",
                    "admin_user": {
                        "email": "admin@empresa.com",
                        "password": "senhasegura123",
                        "username": "admin_empresa",
                        "first_name": "Admin",
                        "last_name": "Empresa"
                    }
                },
                request_only=True,
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        """
        Override create method to enforce company creation rules.
        
        Only the superuser 'adminsentinel' can create companies, and an admin_company
        user must be provided in the request payload.
        """
        # Check if the user is a superuser
        if not request.user.is_superuser:
            return error_response(
                message="Only the platform administrator can create companies.",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        # The serializer will handle validation for admin_user requirements
        return super().create(request, *args, **kwargs)
    
    @transaction.atomic
    def perform_create(self, serializer):
        """
        Create company and log the action within a transaction.
        
        Args:
            serializer: The validated serializer instance
            
        Returns:
            The created company instance
        """
        company = serializer.save()
        logger.info(
            f"Company created: {company.name} (ID: {company.id}) - "
            f"Created by: {self.request.user.username} (ID: {self.request.user.id})"
        )
        return company 