"""
Standard common enums that can be used across multiple modules.
These are enums that are not specific to any single module but represent
shared concepts throughout the application.

Usage examples:

In models:
```python
from api.v1.common.enums import PriorityEnum
from api.core.utils.enum_utils import enum_to_choices

priority = models.CharField(
    max_length=20,
    choices=enum_to_choices(PriorityEnum),
    default=PriorityEnum.MEDIUM.value
)
```

In serializers:
```python
from api.v1.common.enums import PriorityEnum
from api.core.utils.enum_utils import enum_to_choices

priority = serializers.ChoiceField(
    choices=enum_to_choices(PriorityEnum),
    default=PriorityEnum.MEDIUM.value
)
```

In views/viewsets:
```python
from api.v1.common.enums import PriorityEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='priority',
            description='Filter by priority',
            enum=PriorityEnum,
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


class PriorityEnum(str, Enum):
    """Priority enum used across multiple modules"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StatusEnum(str, Enum):
    """Generic status enum that can be used for various entities"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


class TLPEnum(int, Enum):
    """Traffic Light Protocol enum used across security entities"""
    WHITE = 0
    GREEN = 1
    AMBER = 2
    RED = 3


class PAPEnum(int, Enum):
    """Permissible Actions Protocol enum used across security entities"""
    WHITE = 0
    GREEN = 1
    AMBER = 2


class ActionTypeEnum(str, Enum):
    """Common actions that can be performed on entities"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign" 