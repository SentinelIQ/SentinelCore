# SentinelIQ API Documentation

## Overview

This documentation provides comprehensive guidelines and references for developing enterprise-grade API endpoints using the SentinelIQ platform's core architecture. All implementations must follow these standards to ensure consistency, security, and maintainability.

## Table of Contents

### Architecture and Core Components

- [API Core Architecture](./api_core_architecture.md) - Overview of the core components and architecture
- [Audit System](./audit_system.md) - Comprehensive auditing implementation
- [RBAC System](./rbac_system.md) - Role-based access control system
- [Sentry Integration](./sentry-integration.md) - Security monitoring and error tracking

### Standards and Requirements

- [Compliance Requirements](./compliance.md) - Security and regulatory compliance
- [API Tag Structure](./api_tag_structure.md) - OpenAPI documentation standards
- [Celery Configuration](./celery-config.md) - Background task configuration

### Developer Resources

- [API Developer Cheat Sheet](./api_developer_cheatsheet.md) - Quick reference for developers

## Implementation Standards Checklist

All implementations MUST adhere to the following principles:

- ✅ Modular view structure in separate files
- ✅ RBAC enforced on all routes via `api.core.rbac`
- ✅ Standardized API responses from `api.core.responses`
- ✅ Comprehensive audit logging using `api.core.audit`
- ✅ All models registered in Django Admin
- ✅ All API endpoints documented using `@extend_schema`
- ✅ Testing centralized in `/tests/`
- ✅ Tenant isolation enforced on all queries
- ✅ Poetry used for dependency management
- ✅ All commands run inside Docker
- ✅ URLs following kebab-case convention
- ✅ English used for all code and documentation

## Getting Started

New developers should begin by reading the [API Core Architecture](./api_core_architecture.md) document, followed by the [API Developer Cheat Sheet](./api_developer_cheatsheet.md) for a quick reference to common patterns and implementations.

## Command Reference

All commands must be run inside Docker containers:

```bash
# Start the environment
docker compose up -d

# Run Django commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

# Add dependencies
docker compose exec web poetry add package_name

# Run tests
docker compose exec web python manage.py test tests
``` 