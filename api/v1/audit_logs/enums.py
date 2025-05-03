"""
Standard enums for the audit_logs module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.

Usage examples:

In models:
```python
from api.v1.audit_logs.enums import EntityTypeEnum, ActionTypeEnum
from api.core.utils.enum_utils import enum_to_choices

entity_type = models.CharField(
    max_length=50,
    choices=enum_to_choices(EntityTypeEnum),
    default=EntityTypeEnum.OTHER.value
)
```

In serializers:
```python
from api.v1.audit_logs.enums import EntityTypeEnum
from api.core.utils.enum_utils import enum_to_choices

entity_type = serializers.ChoiceField(
    choices=enum_to_choices(EntityTypeEnum),
    default=EntityTypeEnum.OTHER.value
)
```

In views/viewsets:
```python
from api.v1.audit_logs.enums import EntityTypeEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='entity_type',
            description='Filter by entity type',
            enum=EntityTypeEnum,
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


class EntityTypeEnum(str, Enum):
    """Common entity types for audit logs"""
    ALERT = "alert"
    INCIDENT = "incident"
    TASK = "task"
    OBSERVABLE = "observable"
    COMPANY = "company"
    USER = "user"
    SYSTEM = "system"
    OTHER = "other"


class ActionTypeEnum(str, Enum):
    """Common action types for audit logs"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    ESCALATE = "escalate"
    ASSIGN = "assign"
    COMPLETE = "complete"
    CLOSE = "close"
    LOGIN = "login"
    LOGOUT = "logout"
    INGEST = "ingest"
    EXPORT = "export"
    OTHER = "other" 