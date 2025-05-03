"""
Standard enums for the sentinelvision module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.

Usage examples:

In models:
```python
from api.v1.sentinelvision.enums import ModuleTypeEnum
from api.core.utils.enum_utils import enum_to_choices

module_type = models.CharField(
    max_length=20,
    choices=enum_to_choices(ModuleTypeEnum),
    default=ModuleTypeEnum.FEED.value
)
```

In serializers:
```python
from api.v1.sentinelvision.enums import ModuleTypeEnum
from api.core.utils.enum_utils import enum_to_choices

module_type = serializers.ChoiceField(
    choices=enum_to_choices(ModuleTypeEnum),
    default=ModuleTypeEnum.FEED.value
)
```

In views/viewsets:
```python
from api.v1.sentinelvision.enums import ModuleTypeEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='module_type',
            description='Type of module',
            enum=ModuleTypeEnum,
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


class ModuleTypeEnum(str, Enum):
    """SentinelVision module types"""
    FEED = "feed"
    ANALYZER = "analyzer"
    RESPONDER = "responder"


class ModuleStatusEnum(str, Enum):
    """Module execution status"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    RUNNING = "running"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


class FeedTypeEnum(str, Enum):
    """SentinelVision feed types"""
    MISP = "misp"
    TAXII = "taxii"
    STIX = "stix"
    RSS = "rss"
    CSV = "csv"
    TEXT = "text"
    JSON = "json"
    CUSTOM = "custom"


class AnalyzerTypeEnum(str, Enum):
    """SentinelVision analyzer types"""
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE = "file"
    HASH = "hash"
    EMAIL = "email"
    GENERIC = "generic"


class ResponderTypeEnum(str, Enum):
    """SentinelVision responder types"""
    FIREWALL = "firewall"
    EDR = "edr"
    SIEM = "siem"
    EMAIL = "email"
    TICKET = "ticket"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class ExecutionStatusEnum(str, Enum):
    """Execution status for SentinelVision modules"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELED = "canceled"


class SyncStatusEnum(str, Enum):
    """Sync status for SentinelVision feeds"""
    PENDING = "pending"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILURE = "failure"


class ResponderIntegrationTypeEnum(str, Enum):
    """Integration types for responders"""
    FIREWALL = "firewall"
    SOAR = "soar"
    WAF = "waf"
    CUSTOM = "custom" 