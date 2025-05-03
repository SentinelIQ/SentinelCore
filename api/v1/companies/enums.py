"""
Standard enums for the companies module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.

Usage examples:

In models:
```python
from api.v1.companies.enums import CompanyStatusEnum
from api.core.utils.enum_utils import enum_to_choices

status = models.CharField(
    max_length=20,
    choices=enum_to_choices(CompanyStatusEnum),
    default=CompanyStatusEnum.ACTIVE.value
)
```

In serializers:
```python
from api.v1.companies.enums import CompanyStatusEnum
from api.core.utils.enum_utils import enum_to_choices

status = serializers.ChoiceField(
    choices=enum_to_choices(CompanyStatusEnum),
    default=CompanyStatusEnum.ACTIVE.value
)
```

In views/viewsets:
```python
from api.v1.companies.enums import CompanyStatusEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='status',
            description='Filter by company status',
            enum=CompanyStatusEnum,
            required=False
        )
    ]
)
def list(self, request):
    # View implementation
    pass
```
"""
from enum import Enum


class CompanyStatusEnum(str, Enum):
    """Company status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class CompanyTypeEnum(str, Enum):
    """Company type enum"""
    ENTERPRISE = "enterprise"
    SMB = "smb"
    GOVERNMENT = "government"
    EDUCATION = "education"
    NONPROFIT = "nonprofit"
    HEALTHCARE = "healthcare"
    FINANCIAL = "financial"
    OTHER = "other" 