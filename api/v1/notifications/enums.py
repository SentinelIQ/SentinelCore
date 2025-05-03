"""
Standard enums for the notifications module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.
"""
from enum import Enum


class NotificationChannelTypeEnum(str, Enum):
    """Notification channel type enum"""
    EMAIL = "email"
    SLACK = "slack"
    MATTERMOST = "mattermost"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SMS = "sms"


class NotificationEventTypeEnum(str, Enum):
    """Notification event type enum"""
    ALERT_CREATED = "alert_created"
    ALERT_UPDATED = "alert_updated"
    ALERT_ESCALATED = "alert_escalated"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_UPDATED = "incident_updated"
    INCIDENT_CLOSED = "incident_closed"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    CUSTOM = "custom"


class NotificationPriorityEnum(str, Enum):
    """Notification priority enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationCategoryEnum(str, Enum):
    """Notification category enum"""
    ALERT = "alert"
    INCIDENT = "incident"
    TASK = "task"
    SYSTEM = "system"
    REPORT = "report"


class NotificationDeliveryStatusEnum(str, Enum):
    """Notification delivery status enum"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed" 