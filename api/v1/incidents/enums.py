"""
Standard enums for the incidents module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.
"""
from enum import Enum


class IncidentSeverityEnum(str, Enum):
    """Incident severity levels enum"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatusEnum(str, Enum):
    """Incident status enum"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentTLPEnum(int, Enum):
    """Traffic Light Protocol classification enum"""
    WHITE = 0
    GREEN = 1
    AMBER = 2
    RED = 3


class IncidentPAPEnum(int, Enum):
    """Permissible Actions Protocol classification enum"""
    WHITE = 0
    GREEN = 1
    AMBER = 2


class TimelineEventTypeEnum(str, Enum):
    """Timeline event type enum"""
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    ALERT_LINKED = "alert_linked"
    TASK_ADDED = "task_added"
    TASK_COMPLETED = "task_completed"
    NOTE = "note"
    ACTION = "action"
    SYSTEM = "system"
    CLOSED = "closed"
    OTHER = "other"


class IncidentTaskStatusEnum(str, Enum):
    """Incident task status enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled" 