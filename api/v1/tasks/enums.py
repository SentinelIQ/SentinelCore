"""
Standard enums for the tasks module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.
"""
from enum import Enum


class TaskStatusEnum(str, Enum):
    """Task status enum"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class TaskPriorityEnum(str, Enum):
    """Task priority enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical" 