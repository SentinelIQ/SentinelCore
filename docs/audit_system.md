# SentinelIQ Audit System

## Overview

The SentinelIQ Audit System provides comprehensive tracking of all activities in the platform, ensuring compliance with enterprise security standards, regulatory requirements, and providing a detailed history of changes for forensic analysis and accountability.

## Core Components

The audit system is built on multiple components that work together to provide a comprehensive audit trail:

### 1. Model-Level Auditing (`api.core.audit_registration`)

The foundation of the audit system is the automatic tracking of all changes to model instances:

```python
# Automatically register models for auditing
from api.core.audit_registration import register_all_models

# In apps.py or a Django startup hook
register_all_models()
```

Individual model registration:

```python
from auditlog.registry import auditlog
from .models import YourModel

# Register with field exclusions (for sensitive data)
auditlog.register(YourModel, exclude=['password', 'security_key'])
```

### 2. ViewSet Integration (`api.core.audit.AuditLogMixin`)

The `AuditLogMixin` automatically adds audit logging to ViewSet operations:

```python
from api.core.audit import AuditLogMixin
from api.core.viewsets import StandardViewSet

class YourModelViewSet(AuditLogMixin, StandardViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    entity_type = 'your_model'  # Required for audit identification
```

Key capabilities:
- Automatic auditing of create, update, and delete operations
- Capturing the user who performed the action
- Recording the entity type and ID
- Including company/tenant information
- Capturing client IP address

### 3. Custom Action Auditing (`api.core.audit.audit_action`)

For custom actions that don't map to standard CRUD operations:

```python
from api.core.audit import audit_action
from rest_framework.decorators import action

class YourModelViewSet(AuditLogMixin, StandardViewSet):
    # ... existing code ...
    
    @action(detail=True, methods=['post'])
    @audit_action(action_type='approve', entity_type='your_model')
    def approve(self, request, pk=None):
        # Custom approval logic
        return success_response(...)
```

### 4. Task Auditing (`api.core.audit.AuditLogTaskMixin` and `audit_task`)

For background tasks and scheduled operations:

```python
from api.core.audit import AuditLogTaskMixin
from celery import Task

class AuditedTask(AuditLogTaskMixin, Task):
    entity_type = 'scheduled_operation'
    
    def run(self, *args, **kwargs):
        # Task implementation
        pass
```

For function-based tasks:

```python
from api.core.audit import audit_task

@audit_task(entity_type='data_processing')
def process_data(user_id, data_id):
    # Processing logic
    pass
```

### 5. Security Event Monitoring (`api.core.audit_sentry`)

Enhanced security monitoring for critical operations:

```python
from api.core.audit_sentry import security_critical

class UserPermissionView(APIView):
    @security_critical(event_name='permission_change', level='warning')
    def post(self, request):
        # Permission modification logic
        return Response(...)
```

### 6. Audit API Access (`api.core.audit`)

For tracking read-only operations and API access:

```python
from api.core.audit import log_api_access

class YourReadOnlyView(APIView):
    def get(self, request):
        # Process request
        result = ...
        
        # Log access with custom data
        log_api_access(
            user=request.user,
            method=request.method,
            path=request.path,
            status_code=200,
            additional_data={
                'resource_id': resource_id,
                'filters': request.query_params
            }
        )
        
        return Response(result)
```

## Audit Data Structure

Each audit log entry contains:

- **Actor**: The user who performed the action
- **Action**: The type of action (create, update, delete, custom)
- **Entity Type**: The type of entity being acted upon
- **Entity ID**: The specific entity instance ID
- **Timestamp**: When the action occurred
- **Changes**: What fields were changed and their values (for updates)
- **Metadata**: Additional context information
  - Client IP
  - Request method and path
  - Company/tenant information
  - Custom action-specific data

## Implementation Guide

### 1. Register Models for Auditing

Update the `api.core.audit_registration` module to include your models:

```python
def register_your_models():
    """Register your models for auditing."""
    try:
        # Import models
        YourModel = get_model('your_app', 'YourModel')
        
        # Register YourModel for auditing
        if YourModel:
            auditlog.register(YourModel)
            logger.info(f"Registered YourModel for auditing")
            
    except Exception as e:
        logger.error(f"Error registering your models for auditing: {str(e)}")

# Add to register_all_models function
def register_all_models():
    # ... existing registrations
    register_your_models()
    # ...
```

### 2. Apply AuditLogMixin to ViewSets

```python
from api.core.audit import AuditLogMixin

class YourModelViewSet(AuditLogMixin, StandardViewSet):
    entity_type = 'your_model'  # Required
    
    # Optional: add custom audit data
    def get_additional_log_data(self, request, obj=None, action=None):
        data = super().get_additional_log_data(request, obj, action)
        
        # Add custom context data
        if action == 'create':
            data['source_system'] = request.data.get('source')
        
        return data
```

### 3. Custom Audit Events

For operations not tied to a model or ViewSet:

```python
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType

def log_custom_business_event(user, action_name, obj, details=None):
    """Log a custom business event."""
    content_type = ContentType.objects.get_for_model(obj.__class__)
    
    # Map action name to LogEntry action constants
    action_map = {
        'view': LogEntry.Action.ACCESS,
        'create': LogEntry.Action.CREATE,
        'update': LogEntry.Action.UPDATE,
        'delete': LogEntry.Action.DELETE,
    }
    action = action_map.get(action_name, LogEntry.Action.CREATE)
    
    # Create the log entry
    LogEntry.objects.create(
        content_type=content_type,
        object_pk=str(obj.pk),
        object_repr=str(obj),
        action=action,
        actor=user,
        additional_data=details or {}
    )
```

## Security and Privacy Considerations

1. **Exclude Sensitive Data**:
   ```python
   auditlog.register(User, exclude=['password', 'security_question_answer'])
   ```

2. **Mask Personally Identifiable Information (PII)**:
   ```python
   def get_additional_log_data(self, request, obj=None, action=None):
       data = super().get_additional_log_data(request, obj, action)
       
       # Mask PII in logs
       if 'ssn' in data:
           data['ssn'] = 'XXX-XX-' + data['ssn'][-4:]
       
       return data
   ```

3. **Retention Policies**:
   The audit system includes scheduled tasks to comply with data retention policies.
   
   ```python
   # In a scheduled task
   from api.core.audit import clean_audit_logs
   
   def cleanup_old_logs():
       # Clean logs older than 1 year (or per compliance requirements)
       clean_audit_logs(days=365)
   ```

## Audit Log Viewing

Audit logs can be viewed through:

1. **Django Admin Interface**: Configured for authorized administrators
2. **Audit API**: Secured endpoints for querying audit history
3. **Sentry Dashboard**: For security-critical events
4. **Log Files**: Raw audit logs are written to `logs/audit.log`

## Anomaly Detection

The audit system includes baseline behavior analysis and anomaly detection:

```python
from api.core.audit_sentry import detect_anomalies

# In a scheduled task
def check_for_anomalies():
    # Look back 24 hours, alert on 10+ standard deviations from baseline
    detect_anomalies(lookback_hours=24, threshold=10)
```

## Best Practices

1. **Always set `entity_type` on ViewSets and Tasks**
2. **Use `audit_action` for all custom actions**
3. **Register all models with the audit system**
4. **Exclude sensitive fields from audit logs**
5. **Add appropriate indexes for audit log queries**
6. **Use `security_critical` for high-impact operations**

## Sample Implementation

```python
# models.py
class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# audit_registration.py
def register_document_models():
    Document = get_model('documents', 'Document')
    if Document:
        auditlog.register(Document)

# views.py
class DocumentViewSet(AuditLogMixin, StandardViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [HasEntityPermission]
    entity_type = 'document'
    
    def get_queryset(self):
        return super().get_queryset().filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        return serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    @audit_action(action_type='publish', entity_type='document')
    def publish(self, request, pk=None):
        document = self.get_object()
        document.status = 'published'
        document.save()
        return success_response(data=DocumentSerializer(document).data)
```

## Integration with Sentry

Security events captured by the audit system are automatically sent to Sentry with enhanced context:

```python
# Automatically called when security-critical operations are audited
def _process_security_event(log_entry):
    """Process a security-relevant audit log entry and report to Sentry."""
    if not SENTRY_AVAILABLE:
        return
    
    # Set user context
    if log_entry.actor:
        set_user({
            "id": str(log_entry.actor.id),
            "username": log_entry.actor.username,
            "email": getattr(log_entry.actor, 'email', None)
        })
    
    # Set audit context
    set_context("audit_event", {
        "action": log_entry.get_action_display(),
        "resource_type": log_entry.content_type.model if log_entry.content_type else 'unknown',
        "resource_id": log_entry.object_pk,
        "timestamp": log_entry.timestamp.isoformat(),
        "changes": log_entry.changes,
        "additional_data": log_entry.additional_data
    })
    
    # Send to Sentry
    capture_message(
        f"Security audit: {log_entry.get_action_display()} on {log_entry.content_type.model if log_entry.content_type else 'unknown'}",
        level="info"
    )
``` 