"""
This file is a redirection layer to maintain backward compatibility.
All new code should use the serializers from api/v1/companies/serializers.
"""
from api.v1.companies.serializers import (
    CompanySerializer,
    CompanyDetailSerializer,
    UserNestedSerializer,
    CompanyCreateSerializer
)

__all__ = [
    'CompanySerializer',
    'CompanyDetailSerializer',
    'UserNestedSerializer',
    'CompanyCreateSerializer'
] 