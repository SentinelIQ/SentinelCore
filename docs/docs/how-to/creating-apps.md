---
sidebar_position: 1
---

# Creating New Apps

This guide explains how to create new apps in SentinelIQ following the enterprise-grade standards and modular architecture.

## Overview

SentinelIQ organizes functionality into modular apps, each with a clear responsibility. When creating a new app, you must follow the prescribed structure and standards to ensure consistency, maintainability, and proper integration with core components.

## Prerequisites

Before creating a new app, ensure you have:

1. Docker and Docker Compose installed
2. The SentinelIQ project cloned and running
3. Poetry installed in the container
4. Understanding of Django and DRF basics

## Step 1: Create the App Using Django's startapp Command

Always use Django's `startapp` command to create a new app. **Never** create app directories manually.

```bash
# Inside the Docker container
docker compose exec web python manage.py startapp myapp
```

This creates the basic Django app structure:

```
myapp/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
│   └── __init__.py
├── models.py
├── tests.py
└── views.py
```

## Step 2: Organize the App Following Modular Structure

Reorganize the app to follow SentinelIQ's modular structure:

```bash
# Inside the Docker container
cd myapp

# Create the required directories
mkdir -p views serializers permissions filters
touch views/__init__.py serializers/__init__.py permissions/__init__.py filters/__init__.py
```

Your app should now have this structure:

```
myapp/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
│   └── __init__.py
├── models.py
├── views/
│   └── __init__.py
├── serializers/
│   └── __init__.py
├── permissions/
│   └── __init__.py
└── filters/
│   └── __init__.py
└── urls.py
```

## Step 3: Define Models

Define your models in the `models.py` file or, for complex apps, in a models directory:

```python
# myapp/models.py
import uuid
from django.db import models

class MyResource(models.Model):
    """
    My resource description.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('archived', 'Archived'),
        ],
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_resources'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='resources'
    )

    def __str__(self):
        return self.title
```

For complex apps with multiple related models, create a models directory:

```
myapp/
├── models/
│   ├── __init__.py
│   ├── resource.py
│   └── related.py
```

## Step 4: Create Serializers

Create serializers for your models. Follow the pattern of separating serializers by function:

```python
# myapp/serializers/__init__.py
from .base import MyResourceBaseSerializer
from .create import MyResourceCreateSerializer
from .detail import MyResourceDetailSerializer

__all__ = [
    'MyResourceBaseSerializer',
    'MyResourceCreateSerializer',
    'MyResourceDetailSerializer',
]
```

```python
# myapp/serializers/base.py
from rest_framework import serializers
from ..models import MyResource

class MyResourceBaseSerializer(serializers.ModelSerializer):
    """Base serializer for MyResource."""
    
    class Meta:
        model = MyResource
        fields = ['id', 'title', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
```

```python
# myapp/serializers/create.py
from .base import MyResourceBaseSerializer

class MyResourceCreateSerializer(MyResourceBaseSerializer):
    """Serializer for creating MyResource."""
    
    class Meta(MyResourceBaseSerializer.Meta):
        fields = MyResourceBaseSerializer.Meta.fields + ['description']
```

```python
# myapp/serializers/detail.py
from .base import MyResourceBaseSerializer

class MyResourceDetailSerializer(MyResourceBaseSerializer):
    """Serializer for detailed MyResource representation."""
    
    class Meta(MyResourceBaseSerializer.Meta):
        fields = MyResourceBaseSerializer.Meta.fields + ['description', 'created_by']
```

## Step 5: Add Entity-Specific Permissions

Create permission classes specific to your entity:

```python
# myapp/permissions/__init__.py
from .resource import HasMyResourcePermission

__all__ = ['HasMyResourcePermission']
```

```python
# myapp/permissions/resource.py
from api.core.rbac import HasEntityPermission

class HasMyResourcePermission(HasEntityPermission):
    """Permission class for MyResource."""
    entity_type = 'my_resource'
```

## Step 6: Create View Mixins

Create view mixins for different aspects of your resource:

```python
# myapp/views/resource_create.py
from api.core.responses import created_response
from ..serializers import MyResourceCreateSerializer
from ..models import MyResource

class MyResourceCreateMixin:
    """Mixin for creating MyResource."""
    
    def create(self, request, *args, **kwargs):
        serializer = MyResourceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save with company from request
        instance = serializer.save(
            company=request.user.company,
            created_by=request.user
        )
        
        # Log the action
        self.log_action('create', instance)
        
        return created_response(
            data=serializer.data,
            message="Resource created successfully"
        )
```

```python
# myapp/views/resource_detail.py
from api.core.responses import success_response, no_content_response
from ..serializers import MyResourceDetailSerializer
from ..models import MyResource

class MyResourceDetailMixin:
    """Mixin for detail actions on MyResource."""
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = MyResourceDetailSerializer(instance)
        
        # Log the action
        self.log_action('retrieve', instance)
        
        return success_response(
            data=serializer.data,
            message="Resource retrieved successfully"
        )
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = MyResourceDetailSerializer(
            instance, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        
        # Log the action
        self.log_action('update', updated_instance)
        
        return success_response(
            data=serializer.data,
            message="Resource updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Log the action before deletion
        self.log_action('delete', instance)
        
        instance.delete()
        
        return no_content_response(
            message="Resource deleted successfully"
        )
```

```python
# myapp/views/resource_actions.py
from rest_framework.decorators import action
from api.core.responses import success_response
from ..models import MyResource
from ..serializers import MyResourceDetailSerializer

class MyResourceActionsMixin:
    """Mixin for custom actions on MyResource."""
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        instance = self.get_object()
        instance.status = 'active'
        instance.save()
        
        # Log the custom action
        self.log_action('activate', instance)
        
        serializer = MyResourceDetailSerializer(instance)
        return success_response(
            data=serializer.data,
            message="Resource activated successfully"
        )
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        instance = self.get_object()
        instance.status = 'archived'
        instance.save()
        
        # Log the custom action
        self.log_action('archive', instance)
        
        serializer = MyResourceDetailSerializer(instance)
        return success_response(
            data=serializer.data,
            message="Resource archived successfully"
        )
```

## Step 7: Create ViewSet

Combine the mixins into a ViewSet:

```python
# myapp/views/__init__.py
from rest_framework.viewsets import ViewSet
from api.core.viewsets import StandardViewSet
from api.core.audit import AuditLogMixin
from ..permissions import HasMyResourcePermission
from ..models import MyResource
from .resource_create import MyResourceCreateMixin
from .resource_detail import MyResourceDetailMixin
from .resource_actions import MyResourceActionsMixin

class MyResourceViewSet(
    MyResourceCreateMixin,
    MyResourceDetailMixin,
    MyResourceActionsMixin,
    AuditLogMixin,
    StandardViewSet
):
    """ViewSet for MyResource management."""
    permission_classes = [HasMyResourcePermission]
    queryset = MyResource.objects.all()
    audit_entity_type = 'my_resource'
    
    def get_queryset(self):
        """Filter queryset by user's company."""
        return super().get_queryset().filter(company=self.request.user.company)
```

## Step 8: Add URLs

Create a `urls.py` file:

```python
# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyResourceViewSet

router = DefaultRouter()
router.register('my-resources', MyResourceViewSet, basename='my-resource')

urlpatterns = [
    path('', include(router.urls)),
    # Add custom URLs if needed
    path('my-resources/<uuid:pk>/activate/', 
         MyResourceViewSet.as_view({'post': 'activate'}),
         name='my-resource-activate'),
    path('my-resources/<uuid:pk>/archive/',
         MyResourceViewSet.as_view({'post': 'archive'}),
         name='my-resource-archive'),
]
```

## Step 9: Register Models in Admin

Register your models in the Django admin:

```python
# myapp/admin.py
from django.contrib import admin
from .models import MyResource

@admin.register(MyResource)
class MyResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'created_at', 'updated_at', 'company']
    list_filter = ['status', 'company']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_queryset(self, request):
        """Limit resources to user's company unless superuser."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)
```

## Step 10: Add App to INSTALLED_APPS

Register your app in the Django settings:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'myapp',
    # ...
]
```

## Step 11: Register the App's URLs

Add your app's URLs to the main URL configuration:

```python
# api/v1/urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path('', include('myapp.urls')),
    # ...
]
```

## Step 12: Create Tests in `/tests/` Directory

Create tests in the centralized `/tests/` directory, not in the app itself:

```
tests/
└── myapp/
    ├── test_resource_create.py
    ├── test_resource_update.py
    ├── test_resource_delete.py
    └── test_resource_actions.py
```

Example test:

```python
# tests/myapp/test_resource_create.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User
from companies.models import Company
from myapp.models import MyResource

class MyResourceCreateTests(APITestCase):
    """Tests for resource creation."""
    
    def setUp(self):
        """Set up test environment."""
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            company=self.company
        )
        self.client.force_authenticate(user=self.user)
        
    def test_create_resource(self):
        """Test creating a resource."""
        url = reverse('my-resource-list')
        data = {
            'title': 'Test Resource',
            'description': 'Test description',
            'status': 'draft'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['title'], 'Test Resource')
        self.assertEqual(MyResource.objects.count(), 1)
        self.assertEqual(MyResource.objects.get().title, 'Test Resource')
```

## Step 13: Register for Audit Logging

Register your models for audit logging in the app's `apps.py`:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    
    def ready(self):
        """Register models for audit logging."""
        from audit_logs.integration import register_all_models
        register_all_models(app_labels=['myapp'])
```

## Step 14: Document with OpenAPI

Document your API endpoints using `@extend_schema`:

```python
# myapp/views/__init__.py
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes

@extend_schema_view(
    list=extend_schema(
        summary="List resources",
        description="Returns a list of resources for the authenticated user's company.",
        tags=["My Resources"]
    ),
    retrieve=extend_schema(
        summary="Get resource details",
        description="Returns detailed information about a specific resource.",
        tags=["My Resources"]
    ),
    create=extend_schema(
        summary="Create resource",
        description="Creates a new resource for the authenticated user's company.",
        tags=["My Resources"]
    ),
    update=extend_schema(
        summary="Update resource",
        description="Updates an existing resource.",
        tags=["My Resources"]
    ),
    destroy=extend_schema(
        summary="Delete resource",
        description="Deletes a resource.",
        tags=["My Resources"]
    ),
    activate=extend_schema(
        summary="Activate resource",
        description="Activates a draft resource.",
        tags=["My Resources"]
    ),
    archive=extend_schema(
        summary="Archive resource",
        description="Archives an active resource.",
        tags=["My Resources"]
    ),
)
class MyResourceViewSet(
    # ... existing mixins and base classes
):
    # ... existing code
```

## Step 15: Run Migrations

Create and run migrations for your models:

```bash
# Inside the Docker container
docker compose exec web python manage.py makemigrations myapp
docker compose exec web python manage.py migrate
```

## Best Practices

1. **Follow the Modular Structure** - Always organize your app according to the prescribed modular structure
2. **Use Core Components** - Always use the core components from `api.core`
3. **Document All Endpoints** - Use `@extend_schema` to document all API endpoints
4. **Create Tests** - Always create tests in the `/tests/` directory
5. **Register for Audit Logging** - Always register your models for audit logging
6. **Use Kebab-case URLs** - Use kebab-case for all URL patterns
7. **Implement RBAC** - Always implement RBAC for all endpoints
8. **Register in Admin** - Always register your models in the Django admin
9. **Centralized Error Handling** - Let the core error handling handle exceptions
10. **Standardized Responses** - Use the response helpers from `api.core.responses`

## Example Repository Structure After Adding a New App

```
project_root/
├── api/
│   ├── core/            # Core components
│   └── v1/              
│       ├── alerts/      # Existing app
│       ├── incidents/   # Existing app
│       ├── myapp/       # New app
│       │   ├── views/
│       │   │   ├── __init__.py
│       │   │   ├── resource_create.py
│       │   │   ├── resource_detail.py
│       │   │   └── resource_actions.py
│       │   ├── serializers/
│       │   ├── permissions/
│       │   ├── filters/
│       │   ├── admin.py
│       │   ├── apps.py
│       │   ├── models.py
│       │   └── urls.py
│       └── ...
├── tests/
│   ├── alerts/
│   ├── incidents/
│   ├── myapp/           # Tests for new app
│   │   ├── test_resource_create.py
│   │   ├── test_resource_update.py
│   │   ├── test_resource_delete.py
│   │   └── test_resource_actions.py
│   └── ...
├── audit_logs/          # Centralized audit logs
└── ...
```

By following these steps and best practices, you'll create a new app that seamlessly integrates with the SentinelIQ platform and adheres to all enterprise-grade standards. 