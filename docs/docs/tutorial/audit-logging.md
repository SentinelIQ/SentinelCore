---
sidebar_position: 7
---

# Audit Logging

SentinelIQ implements a comprehensive audit logging system to track all significant actions across the platform. This guide explains how to use and integrate with the audit logging system.

## Overview

The audit logging system captures:

- **User Actions** - CRUD operations, logins, custom actions
- **System Actions** - Automated tasks, system changes
- **Context Information** - IP, user agent, timestamp, tenant
- **Data Changes** - Before/after state of modified data

This information is crucial for security monitoring, compliance, and debugging.

## Audit Log Model

The central model in the audit logging system is `AuditLog`:

```python
# audit_logs/models.py
class AuditLog(models.Model):
    """Model for storing audit log entries."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    actor_name = models.CharField(max_length=255)  # For display and system actions
    action = models.CharField(max_length=50)  # create, update, delete, etc.
    entity_type = models.CharField(max_length=50)  # alert, incident, user, etc.
    entity_id = models.UUIDField(null=True)
    entity_name = models.CharField(max_length=255, blank=True)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_data = models.JSONField(null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
```

## Integration Methods

SentinelIQ provides multiple ways to integrate with the audit logging system:

### 1. ViewSet Mixin

The most common approach is to use the `AuditLogMixin` with your ViewSets:

```python
from audit_logs.mixins import AuditLogMixin

class ResourceViewSet(AuditLogMixin, ViewSet):
    audit_entity_type = 'resource'
    
    def perform_create(self, serializer):
        resource = serializer.save()
        self.log_action('create', resource)
        return resource
        
    def perform_update(self, serializer):
        resource = serializer.save()
        self.log_action('update', resource)
        return resource
        
    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()
```

### 2. Signal-Based Tracking

For automatic tracking based on model changes:

```python
# In your app's apps.py
from django.apps import AppConfig

class ResourcesConfig(AppConfig):
    name = 'resources'
    
    def ready(self):
        from audit_logs.integration import register_model_for_auditing
        from .models import Resource
        
        register_model_for_auditing(
            Resource,
            exclude_fields=['password', 'sensitive_data']
        )
```

### 3. Function Decorator

For function-based views or custom actions:

```python
from audit_logs.decorators import audit_action

@audit_action(entity_type='resource', action='custom_action')
def custom_resource_action(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    # Process action...
    return response
```

### 4. Manual Logging

For complete control:

```python
from audit_logs.api import log_manually

def complex_operation(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    # Perform operations...
    
    log_manually(
        request=request,
        actor=request.user,
        action='complex_operation',
        entity_type='resource',
        entity_id=resource.id,
        entity_name=resource.name,
        metadata={'custom_field': 'value'}
    )
    
    return response
```

## Celery Task Integration

For background tasks, use the `AuditLogTaskMixin`:

```python
from audit_logs.mixins import AuditLogTaskMixin
from celery import Task

class ResourceProcessingTask(AuditLogTaskMixin, Task):
    audit_entity_type = 'resource'
    
    def run(self, resource_id):
        resource = Resource.objects.get(id=resource_id)
        # Process resource...
        self.log_task_action('process', resource)
```

## Querying Audit Logs

To retrieve audit logs:

```python
from audit_logs.query import get_audit_logs

# Get all create actions for resources in the last 30 days
logs = get_audit_logs(
    entity_type='resource',
    action='create',
    company=request.user.company,
    start_date=datetime.now() - timedelta(days=30)
)
```

## Sensitive Data Handling

The audit logging system sanitizes sensitive data:

```python
# audit_logs/sanitize.py
def sanitize_data(data, sensitive_fields=None):
    """Sanitize data to remove sensitive information."""
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']
    
    sanitized = copy.deepcopy(data)
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '********'
    
    return sanitized
```

## Tenant Isolation

All audit logs are automatically isolated by tenant/company:

```python
def get_company_audit_logs(company, **filters):
    """Get audit logs for a specific company."""
    return AuditLog.objects.filter(company=company, **filters)
```

## Best Practices

1. **Log All Significant Actions** - Create, update, delete, and custom actions
2. **Include Relevant Context** - User, timestamp, IP, request data
3. **Sanitize Sensitive Data** - Never log passwords or sensitive information
4. **Use Descriptive Actions** - Use clear action names like 'escalate', 'approve'
5. **Include Metadata** - Add relevant metadata for complex actions
6. **Isolate by Tenant** - Always include company context

## Example: Complete Audit Log Implementation

```python
# views.py
from audit_logs.mixins import AuditLogMixin
from rest_framework.viewsets import ModelViewSet

class IncidentViewSet(AuditLogMixin, ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    audit_entity_type = 'incident'
    
    def get_queryset(self):
        return super().get_queryset().filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        incident = serializer.save(company=self.request.user.company, created_by=self.request.user)
        self.log_action('create', incident)
        return incident
    
    def perform_update(self, serializer):
        incident = serializer.save()
        self.log_action('update', incident)
        return incident
    
    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        incident = self.get_object()
        incident.status = 'closed'
        incident.closed_at = timezone.now()
        incident.closed_by = request.user
        incident.save()
        
        self.log_action(
            'close', 
            incident, 
            metadata={'reason': request.data.get('reason')}
        )
        
        serializer = self.get_serializer(incident)
        return Response(serializer.data)
```

By following these guidelines, you'll ensure comprehensive audit trails across your application, supporting security, compliance, and debugging needs. 