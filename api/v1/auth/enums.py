"""
Standard enums for the auth module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.
"""
from enum import Enum


class UserRoleEnum(str, Enum):
    """User role enum"""
    ADMIN_COMPANY = "admin_company"
    ANALYST_COMPANY = "analyst_company"
    READ_ONLY = "read_only"
    SUPERUSER = "superuser" 