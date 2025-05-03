"""
Standard enums for the alerts module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.

Usage examples:

In models:
```python
from api.v1.alerts.enums import AlertStatusEnum
from api.core.utils.enum_utils import enum_to_choices

status = models.CharField(
    max_length=20,
    choices=enum_to_choices(AlertStatusEnum),
    default=AlertStatusEnum.NEW.value
)
```

In serializers:
```python
from api.v1.alerts.enums import AlertStatusEnum
from api.core.utils.enum_utils import enum_to_choices

status = serializers.ChoiceField(
    choices=enum_to_choices(AlertStatusEnum),
    default=AlertStatusEnum.NEW.value
)
```

In views/viewsets:
```python
from api.v1.alerts.enums import AlertStatusEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='status',
            description='Filter by alert status',
            enum=AlertStatusEnum,
            required=False
        )
    ]
)
def list(self, request):
    # View implementation
    pass
"""
from enum import Enum


class AlertSeverityEnum(str, Enum):
    """Alert severity levels enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatusEnum(str, Enum):
    """Alert status enum"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class AlertTLPEnum(int, Enum):
    """Traffic Light Protocol classification enum"""
    WHITE = 0
    GREEN = 1
    AMBER = 2
    RED = 3


class AlertPAPEnum(int, Enum):
    """Permissible Actions Protocol classification enum"""
    WHITE = 0
    GREEN = 1
    AMBER = 2 