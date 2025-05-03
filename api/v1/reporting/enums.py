"""
Standard enums for the reporting module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.

Usage examples:

In models:
```python
from api.v1.reporting.enums import ReportFormatEnum
from api.core.utils.enum_utils import enum_to_choices

report_format = models.CharField(
    max_length=20,
    choices=enum_to_choices(ReportFormatEnum),
    default=ReportFormatEnum.PDF.value
)
```

In serializers:
```python
from api.v1.reporting.enums import ReportFormatEnum
from api.core.utils.enum_utils import enum_to_choices

report_format = serializers.ChoiceField(
    choices=enum_to_choices(ReportFormatEnum),
    default=ReportFormatEnum.PDF.value
)
```

In views/viewsets:
```python
from api.v1.reporting.enums import ReportFormatEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='format',
            description='Report format',
            enum=ReportFormatEnum,
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


class ReportFormatEnum(str, Enum):
    """Report format types"""
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class ReportTemplateEnum(str, Enum):
    """Report template types"""
    DEFAULT = "default"
    EXECUTIVE = "executive"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"


class ReportEntityTypeEnum(str, Enum):
    """Entity types that can be reported on"""
    INCIDENT = "incident"
    ALERT = "alert"
    OBSERVABLE = "observable"
    TASK = "task"
    MITRE = "mitre"
    COMPANY = "company" 