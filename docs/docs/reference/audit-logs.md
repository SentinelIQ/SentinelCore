---
sidebar_position: 2
---

# Audit Logs Reference

The `audit_logs` module provides a comprehensive, centralized audit logging system for tracking all significant actions across the SentinelIQ platform. This reference documents the key components of the audit logging system.

## Overview

The audit logs system captures detailed information about user and system actions, providing a complete audit trail for security and compliance purposes. Key features include:

- **Complete Action Tracking** - Log all significant user and system actions
- **Tenant Isolation** - Secure multi-tenant audit trails
- **Detailed Context** - Capture request data, IP, user agent, etc.
- **Query Capabilities** - Advanced filtering and search
- **Integration with Core** - Seamless integration with the rest of the platform

## Models (`audit_logs.models`)

### `AuditLog`

The main model for storing audit log entries.

**Fields:**
- `id` (UUIDField): Primary key
- `timestamp` (DateTimeField): When the action occurred
- `actor` (ForeignKey): User who performed the action (null for system actions)
- `actor_name` (CharField): Name of the actor (for display and system actions)
- `action` (CharField): The action performed (e.g., 'create', 'update', 'delete')
- `entity_type` (CharField): The type of entity acted upon (e.g., 'alert', 'incident')
- `entity_id` (UUIDField): The ID of the entity
- `entity_name` (CharField): The name or description of the entity
- `company` (ForeignKey): The company/tenant context
- `ip_address` (GenericIPAddressField): The IP address of the request
- `user_agent` (TextField): The user agent string
- `request_data` (JSONField): The request data (sanitized)
- `changes` (JSONField): Changes made to the entity
- `metadata` (JSONField): Additional metadata

**Example:**
```python
# Automatically created by the AuditLogMixin
```

## Integration (`audit_logs.integration`)

### Functions

#### `register_model_for_auditing(model_class, exclude_fields=None, include_fields=None)`

Registers a model for automatic audit logging.

**Parameters:**
- `model_class` (Model): The model class to register
- `exclude_fields` (list, optional): Fields to exclude from change tracking. Default: `None`
- `include_fields` (list, optional): Fields to include in change tracking (if specified, only these fields are tracked). Default: `None`

**Example:**
```python
from audit_logs.integration import register_model_for_auditing
from myapp.models import MyModel

register_model_for_auditing(
    MyModel,
    exclude_fields=['password', 'sensitive_data']
)
```

#### `register_all_models(app_labels=None, exclude_models=None)`

Registers all models in specified apps for audit logging.

**Parameters:**
- `app_labels` (list, optional): App labels to register. If None, all apps are registered. Default: `None`
- `exclude_models` (list, optional): Models to exclude. Default: `None`

**Example:**
```python
from audit_logs.integration import register_all_models

register_all_models(
    app_labels=['alerts', 'incidents'],
    exclude_models=['alerts.InternalNote']
)
```

## Mixins (`audit_logs.mixins`)

### `AuditLogMixin`

Mixin that adds audit logging functionality to a viewset.

**Attributes:**
- `audit_entity_type` (str): The type of entity being audited

**Methods:**

#### `log_action(action, obj, **kwargs)`

Logs an action on an object.

**Parameters:**
- `action` (str): The action being performed (e.g., 'create', 'update')
- `obj` (Model): The object being acted upon
- `**kwargs`: Additional data to include in the log

**Example:**
```python
from audit_logs.mixins import AuditLogMixin
from rest_framework.viewsets import ModelViewSet

class AlertViewSet(AuditLogMixin, ModelViewSet):
    audit_entity_type = 'alert'
    
    def perform_create(self, serializer):
        alert = serializer.save()
        self.log_action('create', alert)
        return alert
        
    def perform_update(self, serializer):
        alert = serializer.save()
        self.log_action('update', alert)
        return alert
```

### `AuditLogTaskMixin`

Mixin that adds audit logging functionality to a Celery task.

**Attributes:**
- `audit_entity_type` (str): The type of entity being audited

**Methods:**

#### `log_task_action(action, obj, **kwargs)`

Logs a task action on an object.

**Parameters:**
- `action` (str): The action being performed
- `obj` (Model): The object being acted upon
- `**kwargs`: Additional data to include in the log

**Example:**
```python
from audit_logs.mixins import AuditLogTaskMixin
from celery import Task

class AlertCleanupTask(AuditLogTaskMixin, Task):
    audit_entity_type = 'alert'
    
    def run(self, alert_id):
        alert = Alert.objects.get(id=alert_id)
        # Process alert...
        self.log_task_action('cleanup', alert)
```

## Signals (`audit_logs.signals`)

The audit logs module uses Django signals to automatically track model changes.

### `post_save` Signal Handler

Tracks model creation and updates.

### `post_delete` Signal Handler

Tracks model deletion.

## Decorators (`audit_logs.decorators`)

### `audit_action(entity_type, action)`

Decorator that adds audit logging to a function.

**Parameters:**
- `entity_type` (str): The type of entity being audited
- `action` (str): The action being performed

**Example:**
```python
from audit_logs.decorators import audit_action

@audit_action(entity_type='alert', action='escalate')
def escalate_alert(request, alert_id):
    alert = Alert.objects.get(id=alert_id)
    # Process escalation...
    return alert
```

## API (`audit_logs.api`)

### `log_api_access(request, response, entity_type=None, entity_id=None)`

Logs API access.

**Parameters:**
- `request` (Request): The request object
- `response` (Response): The response object
- `entity_type` (str, optional): The type of entity being accessed. Default: `None`
- `entity_id` (str, optional): The ID of the entity being accessed. Default: `None`

**Example:**
```python
from audit_logs.api import log_api_access

def api_view(request):
    # Process request...
    response = generate_response()
    log_api_access(request, response, 'alert', alert_id)
    return response
```

## Query API (`audit_logs.query`)

### `get_audit_logs(entity_type=None, entity_id=None, actor=None, action=None, company=None, start_date=None, end_date=None)`

Retrieves audit logs with filtering.

**Parameters:**
- `entity_type` (str, optional): Filter by entity type. Default: `None`
- `entity_id` (str, optional): Filter by entity ID. Default: `None`
- `actor` (User, optional): Filter by actor. Default: `None`
- `action` (str, optional): Filter by action. Default: `None`
- `company` (Company, optional): Filter by company. Default: `None`
- `start_date` (datetime, optional): Filter by start date. Default: `None`
- `end_date` (datetime, optional): Filter by end date. Default: `None`

**Returns:**
- `QuerySet`: Filtered audit logs

**Example:**
```python
from audit_logs.query import get_audit_logs

# Get all create actions for alerts
alert_creates = get_audit_logs(
    entity_type='alert',
    action='create',
    start_date=datetime.now() - timedelta(days=30)
)
```

## Data Sanitization (`audit_logs.sanitize`)

### `sanitize_data(data, sensitive_fields=None)`

Sanitizes data to remove sensitive information.

**Parameters:**
- `data` (dict): The data to sanitize
- `sensitive_fields` (list, optional): Fields to sanitize. Default: `None`

**Returns:**
- `dict`: Sanitized data

## Compliance Reporting (`audit_logs.reports`)

### `generate_compliance_report(entity_type=None, start_date=None, end_date=None, company=None)`

Generates a compliance report based on audit logs.

**Parameters:**
- `entity_type` (str, optional): Filter by entity type. Default: `None`
- `start_date` (datetime, optional): Start date for the report. Default: `None`
- `end_date` (datetime, optional): End date for the report. Default: `None`
- `company` (Company, optional): Filter by company. Default: `None`

**Returns:**
- `dict`: Compliance report data

## Usage Examples

### Basic Integration with ViewSet

```python
from audit_logs.mixins import AuditLogMixin
from rest_framework.viewsets import ModelViewSet

class IncidentViewSet(AuditLogMixin, ModelViewSet):
    audit_entity_type = 'incident'
    
    def perform_create(self, serializer):
        incident = serializer.save()
        self.log_action('create', incident)
        return incident
```

### Automatic Model Registration

```python
# In apps.py
from django.apps import AppConfig

class IncidentsConfig(AppConfig):
    name = 'incidents'
    
    def ready(self):
        from audit_logs.integration import register_all_models
        register_all_models(app_labels=['incidents'])
```

### Manual Logging

```python
from audit_logs.api import log_manually

def custom_action(request, incident_id):
    incident = Incident.objects.get(id=incident_id)
    # Perform custom action...
    
    # Log the action
    log_manually(
        request=request,
        actor=request.user,
        action='custom_action',
        entity_type='incident',
        entity_id=incident.id,
        entity_name=incident.title,
        metadata={'custom_field': 'value'}
    )
    
    return response
```

## Best Practices

1. **Use Mixins** - Prefer using the provided mixins for consistent logging
2. **Register Models** - Register models for automatic tracking where appropriate
3. **Sanitize Data** - Ensure sensitive data is properly excluded
4. **Be Descriptive** - Use clear action names and include relevant metadata
5. **Isolate by Tenant** - Always include company context for multi-tenant isolation
6. **Consider Performance** - For high-volume operations, consider using async logging 