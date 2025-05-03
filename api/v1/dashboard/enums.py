"""
Standard enums for the dashboard module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.

Usage examples:

In models:
```python
from api.v1.dashboard.enums import TimeRangeEnum
from api.core.utils.enum_utils import enum_to_choices

time_range = models.CharField(
    max_length=20,
    choices=enum_to_choices(TimeRangeEnum),
    default=TimeRangeEnum.THIRTY_DAYS.value
)
```

In serializers:
```python
from api.v1.dashboard.enums import TimeRangeEnum
from api.core.utils.enum_utils import enum_to_choices

time_range = serializers.ChoiceField(
    choices=enum_to_choices(TimeRangeEnum),
    default=TimeRangeEnum.THIRTY_DAYS.value
)
```

In views/viewsets:
```python
from api.v1.dashboard.enums import TimeRangeEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='time_range',
            description='Time range for dashboard data',
            enum=TimeRangeEnum,
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


class TimeRangeEnum(str, Enum):
    """Dashboard time range options"""
    TODAY = "today"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class WidgetTypeEnum(str, Enum):
    """Dashboard widget types"""
    ALERT_SEVERITY = "alert_severity"
    INCIDENT_TRENDS = "incident_trends"
    RECENT_ALERTS = "recent_alerts"
    RECENT_INCIDENTS = "recent_incidents"
    TASK_COMPLETION = "task_completion"
    MITRE_COVERAGE = "mitre_coverage"
    OBSERVABLES_SUMMARY = "observables_summary"
    SECURITY_METRICS = "security_metrics"
    CUSTOM_METRICS = "custom_metrics"


class ChartTypeEnum(str, Enum):
    """Chart visualization types"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    TABLE = "table"
    CARD = "card"
    HEAT_MAP = "heat_map"
    SCATTER = "scatter" 