---
sidebar_position: 1
---

# Learning SentinelIQ

Welcome to the SentinelIQ learning guide. This section will help you understand the core concepts of SentinelIQ and how to use its features effectively.

## Getting Started

SentinelIQ is an enterprise-grade security platform built with Django REST Framework, focusing on:

1. **Comprehensive Security Monitoring**
2. **Incident Management**
3. **Audit Logging & Compliance**
4. **Multi-tenant Architecture**

## Understanding SentinelIQ Architecture

SentinelIQ follows a modular architecture with several key components:

- **Core Framework** (`api.core`) - Foundation components used across the platform
- **Audit Logging** (`audit_logs`) - Comprehensive activity tracking system
- **Feature Modules** - Specialized functionality (alerts, incidents, tasks, etc.)
- **Infrastructure** - Supporting components for deployment and operations

## Key Concepts

### Modular Structure

The platform is built with clear module boundaries, following Django's app structure but with enhanced organization:

```
<app>/
├── views/           # Split by functionality
├── serializers/     # Data transformation
├── permissions/     # Access control
├── filters/         # Query filtering
```

### Enterprise-grade Standards

All code follows strict enterprise-grade standards:

- **Poetry** for dependency management
- **Docker** for consistent environments
- **RBAC** for comprehensive security
- **Comprehensive testing** with central test organization
- **Thorough documentation** with OpenAPI specifications

### API Response Standardization

All API responses follow a consistent format from `api.core.responses`:

```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully",
  "meta": { 
    "pagination": { ... }
  }
}
```

## Learning Path

To effectively learn SentinelIQ, follow these guides in order:

1. [Django/DRF Fundamentals](django-drf-fundamentals)
2. [Tutorials - Start Here](../tutorial/intro)
3. [Advanced Security Topics](../advanced/rbac-advanced)
4. [How-to Guides](../how-to/creating-apps)

## Development Environment

SentinelIQ requires:

- Docker and Docker Compose
- Poetry for Python dependency management

All development must occur within the Docker container, using the provided commands:

```bash
# Start the environment
docker-compose up -d

# Run Django commands
docker-compose exec web python manage.py <command>

# Add dependencies
docker-compose exec web poetry add <package>
``` 