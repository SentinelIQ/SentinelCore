---
sidebar_position: 2
---

# Django and DRF Fundamentals

Understanding Django and Django REST Framework (DRF) is essential for working with SentinelIQ. This guide provides an overview of key concepts.

## Django Overview

Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. SentinelIQ builds upon Django's core functionality, leveraging:

- **MTV Architecture** (Model-Template-View)
- **ORM** (Object-Relational Mapping) for database interactions
- **Admin Interface** for basic content management
- **Authentication System** for secure user management
- **Middleware Components** for request/response processing

## Django REST Framework

Django REST Framework (DRF) extends Django to build Web APIs. SentinelIQ uses DRF extensively with custom enhancements for:

- **Serialization** - Converting complex data types to Python datatypes that can be rendered into JSON
- **Authentication** - Including JWT and OAuth2 implementations
- **Viewsets & Routers** - Organizing API endpoints
- **Permissions** - Fine-grained access control
- **Content Negotiation** - Handling different media types
- **Pagination** - Managing large result sets
- **Filtering** - Query parameter handling

## Enhanced DRF Components in SentinelIQ

SentinelIQ extends DRF with enterprise-grade enhancements:

### Modular View Structure

Unlike standard DRF views, SentinelIQ separates views by responsibility:

```
views/
├── __init__.py              # Combines view mixins
├── resource_create.py       # Create operations
├── resource_detail.py       # Retrieve/Update/Delete operations
└── resource_custom_actions.py  # Custom endpoints
```

### Enhanced Response Format

Custom response formatters ensure consistent API responses:

```python
# Standard success response
from api.core.responses import success_response

def my_view(request):
    # Process data...
    return success_response(
        data=my_data,
        message="Operation completed successfully",
        status_code=200
    )
```

### Role-Based Access Control (RBAC)

Extended permission classes that integrate with a comprehensive RBAC system:

```python
from api.core.permissions import HasEntityPermission

class MyViewSet(ViewSet):
    permission_classes = [HasEntityPermission]
    entity_type = 'incident'
    # ...
```

### Centralized Test Structure

Unlike Django's typical app-based test organization, SentinelIQ centralizes tests:

```
tests/
├── alerts/
│   ├── test_alert_create.py
│   └── test_alert_escalate.py
├── incidents/
│   └── ...
```

## Development Environment

SentinelIQ's development environment is completely containerized using Docker. Key commands:

```bash
# Start the environment
docker-compose up -d

# Run tests
docker-compose exec web python manage.py test tests

# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

## Key Patterns and Best Practices

When working with SentinelIQ, keep these principles in mind:

1. **Modular Structure** - Maintain clear boundaries between modules
2. **Consistent API Responses** - Always use the response helpers from `api.core.responses`
3. **RBAC for Security** - Always implement proper permissions
4. **Audit Logging** - Integrate all significant actions with the audit log system
5. **OpenAPI Documentation** - Document all endpoints with `@extend_schema`
6. **Centralized Tests** - Place tests in the central `/tests/` directory, not in apps 