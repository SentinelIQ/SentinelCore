---
sidebar_position: 2
---

# Modular Architecture

SentinelIQ implements a highly modular architecture that extends Django's app-based structure with additional organization for enterprise-grade maintainability and scalability.

## Architecture Overview

At a high level, SentinelIQ is organized as follows:

```
project_root/
├── api/
│   ├── core/                # Core framework components
│   └── v1/                  # API version 1
│       ├── alerts/          # Alert management
│       ├── incidents/       # Incident management
│       ├── tasks/           # Task management
│       └── ...
├── audit_logs/              # Centralized audit logging
├── tests/                   # Centralized test suite
│   ├── alerts/
│   ├── incidents/
│   └── ...
├── logs/                    # Application logs
│   ├── api.log
│   ├── error.log
│   └── django.log
└── pyproject.toml           # Poetry dependency management
```

## Enhanced App Structure

Unlike traditional Django apps, SentinelIQ uses an enhanced structure for better organization of complex functionality. Each app follows this pattern:

```
<app>/
├── views/
│   ├── __init__.py          # Combines view mixins
│   ├── resource_create.py   # Create operations
│   ├── resource_detail.py   # Retrieve/Update/Delete
│   └── resource_actions.py  # Custom actions
├── serializers/
│   ├── __init__.py
│   ├── base.py              # Base serializers
│   ├── create.py            # Create-specific serializers
│   ├── detail.py            # Detail-specific serializers
│   └── nested.py            # Nested resource serializers
├── models/
│   ├── __init__.py
│   ├── resource.py          # Main resource model
│   └── related.py           # Related models
├── permissions/
│   ├── __init__.py
│   └── resource.py          # Resource-specific permissions
├── filters/
│   ├── __init__.py
│   └── resource.py          # Resource-specific filters
├── admin.py                 # Admin registration
├── apps.py                  # App configuration
└── urls.py                  # URL routing
```

This structure provides several benefits:

1. **Clear Separation of Concerns** - Each component has a specific responsibility
2. **Better Maintainability** - Smaller, focused files are easier to understand and maintain
3. **Team Collaboration** - Different developers can work on different aspects simultaneously
4. **Testability** - Isolated components are easier to test

## View Organization

Views are organized by their responsibility, rather than traditional Django class-based views:

### View Mixins Pattern

The `views/__init__.py` file combines mixins to create complete viewsets:

```python
# alerts/views/__init__.py
from rest_framework.viewsets import ViewSet

from api.core.viewsets import StandardViewSet
from .alert_create import AlertCreateMixin
from .alert_detail import AlertDetailMixin
from .alert_actions import AlertActionsMixin

class AlertViewSet(
    AlertCreateMixin,
    AlertDetailMixin,
    AlertActionsMixin,
    StandardViewSet
):
    """Alert management viewset."""
    pass
```

### Individual View Components

Each view component handles a specific responsibility:

```python
# alerts/views/alert_create.py
from api.core.responses import created_response
from ..serializers import AlertCreateSerializer

class AlertCreateMixin:
    """Alert creation functionality."""
    
    def create(self, request, *args, **kwargs):
        serializer = AlertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert = serializer.save()
        
        # Audit logging
        self.log_action('create', alert)
        
        return created_response(
            data=serializer.data,
            message="Alert created successfully",
        )
```

## URL Pattern

URLs follow a kebab-case pattern for consistency and readability:

```python
# alerts/urls.py
from rest_framework.routers import DefaultRouter
from .views import AlertViewSet

router = DefaultRouter()
router.register('alerts', AlertViewSet, basename='alert')

urlpatterns = [
    # Additional custom paths
    path('alerts/<uuid:id>/assign-analyst/', AlertViewSet.as_view({'post': 'assign_analyst'})),
    path('alerts/<uuid:id>/escalate/', AlertViewSet.as_view({'post': 'escalate'})),
]
```

## Model Organization

For complex apps with multiple related models, models are organized in separate files:

```python
# incidents/models/incident.py
class Incident(models.Model):
    """Security incident record."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    # ...

# incidents/models/evidence.py
class Evidence(models.Model):
    """Evidence attached to an incident."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey('Incident', on_delete=models.CASCADE, related_name='evidence')
    # ...
```

## Serializer Organization

Serializers are organized by their purpose to maintain clean separation:

```python
# Base serializers for common fields
# incidents/serializers/base.py
class IncidentBaseSerializer(serializers.ModelSerializer):
    """Base serializer for incidents."""
    class Meta:
        model = Incident
        fields = ['id', 'title', 'status', 'created_at', 'updated_at']

# Creation-specific serializers
# incidents/serializers/create.py
class IncidentCreateSerializer(IncidentBaseSerializer):
    """Serializer for incident creation."""
    class Meta(IncidentBaseSerializer.Meta):
        fields = IncidentBaseSerializer.Meta.fields + ['description', 'severity']
        read_only_fields = ['id', 'created_at', 'updated_at']
```

## Cross-Cutting Concerns

Cross-cutting concerns like authentication, permissions, and audit logging are implemented in a centralized manner to ensure consistency:

- **Authentication** - Centralized in the API core
- **Permissions** - Core RBAC implementation with app-specific permissions
- **Audit Logging** - Centralized audit log system used across all apps
- **API Documentation** - Consistent OpenAPI specs using DRF Spectacular

## Practical Benefits

This modular architecture delivers several practical benefits:

1. **Scalability** - The system can grow without becoming unwieldy
2. **Maintainability** - Changes are focused and isolated
3. **Onboarding** - New developers can quickly understand the codebase
4. **Testing** - Clean separation makes testing easier and more focused
5. **Deployment** - Modular services can be deployed independently

In the next section, we'll explore the [core components](core-components) that provide foundational functionality across the platform. 