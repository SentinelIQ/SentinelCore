# SentinelIQ API Developer Cheat Sheet

## Getting Started

### Environment Setup
```bash
# Start containers
docker compose up -d

# Run Django commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

# Add dependencies
docker compose exec web poetry add package_name
```

### Creating a New App
```bash
# Create new Django app
docker compose exec web python manage.py startapp your_app_name
```

### Required App Structure
```
your_app/
├── views/              # Modular view files
├── serializers/        # Serializer classes
├── models.py           # Data models
├── admin.py            # Admin configuration (required)
├── urls.py             # URL configurations
├── filters.py          # Optional filter classes
└── permissions.py      # Optional custom permissions
```

## Core Components Reference

### Response System
```python
from api.core.responses import success_response, error_response, created_response, no_content_response

# Success (200 OK)
return success_response(data=data, message="Operation successful")

# Created (201 Created)
return created_response(data=data, message="Resource created")

# No Content (204 No Content)
return no_content_response()

# Error (400, 500, etc.)
return error_response(message="Error message", errors=serializer.errors, status_code=400)
```

### RBAC Implementation
```python
from api.core.rbac import HasEntityPermission

class YourModelViewSet(viewsets.ModelViewSet):
    permission_classes = [HasEntityPermission]
    entity_type = 'your_model'  # Must match permission matrix
```

### ViewSets
```python
from api.core.viewsets import StandardViewSet, ReadOnlyViewSet
from api.core.rbac import HasEntityPermission
from api.core.audit import AuditLogMixin

# Full CRUD ViewSet
class YourModelViewSet(AuditLogMixin, StandardViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [HasEntityPermission]
    entity_type = 'your_model'
    
    def get_queryset(self):
        # Tenant isolation
        return super().get_queryset().filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        return serializer.save(company=self.request.user.company)
        
# Read-only ViewSet
class YourReadOnlyViewSet(AuditLogMixin, ReadOnlyViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [HasEntityPermission]
    entity_type = 'your_model'
```

### Pagination
```python
from api.core.pagination import StandardResultsSetPagination, LargeResultsSetPagination

class YourModelViewSet(StandardViewSet):
    pagination_class = StandardResultsSetPagination  # 50 items per page
    # pagination_class = LargeResultsSetPagination   # 100 items per page
    # pagination_class = SmallResultsSetPagination   # 10 items per page
```

### Custom Actions
```python
from rest_framework.decorators import action
from api.core.audit import audit_action
from api.core.responses import success_response

class YourModelViewSet(AuditLogMixin, StandardViewSet):
    # ... other code ...
    
    @action(detail=True, methods=['post'], url_path='custom-action')
    @audit_action(action_type='custom_action', entity_type='your_model')
    def custom_action(self, request, pk=None):
        # Implementation
        return success_response(data={'status': 'completed'})
```

### API Documentation
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

class YourModelViewSet(StandardViewSet):
    # ... other code ...
    
    @extend_schema(
        tags=["Your Category"],
        description="Detailed description of the endpoint",
        parameters=[
            OpenApiParameter(name="param_name", type=str, description="Parameter description")
        ],
        responses={201: YourModelSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
```

### Audit & Security
```python
# ViewSet auditing (automatic for CRUD operations)
from api.core.audit import AuditLogMixin

class YourModelViewSet(AuditLogMixin, StandardViewSet):
    entity_type = 'your_model'  # Required for audit

# Custom action auditing
from api.core.audit import audit_action

@audit_action(action_type='custom_action', entity_type='your_model')
def your_method(self, request, pk=None):
    # Implementation

# Security-critical operations
from api.core.audit_sentry import security_critical

@security_critical(event_name='critical_operation')
def security_sensitive_method(self, request, *args, **kwargs):
    # Implementation
```

### Models & Tenant Isolation
```python
from django.db import models

class YourModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Required for tenant isolation
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE,
        related_name='your_models'
    )
    
    # Standard timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'
```

### Admin Registration (Required)
```python
from django.contrib import admin
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'created_at')
    list_filter = ('company',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
```

### URL Pattern (kebab-case required)
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import YourModelViewSet

router = DefaultRouter()
router.register(r'your-models', YourModelViewSet)  # kebab-case
router.register(r'your-models/custom-endpoint', YourCustomViewSet)  # kebab-case

urlpatterns = [
    path('', include(router.urls)),
]
```

### Testing Structure
```python
# In /tests/your_app/test_your_model.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from your_app.models import YourModel
from companies.models import Company
from auth_app.models import User

class YourModelTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            company=self.company
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_create_your_model(self):
        data = {"name": "Test Name", "description": "Test Description"}
        response = self.client.post('/api/v1/your-models/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

## Running Tests
```bash
# Run all tests
docker compose exec web python manage.py test tests

# Run specific app tests
docker compose exec web python manage.py test tests.your_app
```

## Common Mistakes to Avoid

1. ❌ **Don't** use `requirements.txt` - use Poetry instead
2. ❌ **Don't** create apps manually - always use `startapp` command
3. ❌ **Don't** use camelCase in URLs - use kebab-case
4. ❌ **Don't** forget tenant isolation in `get_queryset()`
5. ❌ **Don't** skip audit logging or model registration
6. ❌ **Don't** forget to document API endpoints
7. ❌ **Don't** place tests in the app directory
8. ❌ **Don't** commit code with TODOs or placeholders
9. ❌ **Don't** forget to register models in Django Admin

## Quick Template for New ViewSet

```python
from rest_framework import viewsets
from api.core.viewsets import StandardViewSet
from api.core.rbac import HasEntityPermission
from api.core.audit import AuditLogMixin
from api.core.pagination import StandardResultsSetPagination
from drf_spectacular.utils import extend_schema
from .models import YourModel
from .serializers import YourModelSerializer

@extend_schema(tags=["Your Category"])
class YourModelViewSet(AuditLogMixin, StandardViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [HasEntityPermission]
    entity_type = 'your_model'
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Enforce tenant isolation
        return super().get_queryset().filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # Assign company automatically
        return serializer.save(company=self.request.user.company)
``` 