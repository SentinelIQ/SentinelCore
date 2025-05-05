---
sidebar_position: 1
---

# SentinelIQ Tutorial - Introduction

Welcome to the SentinelIQ tutorial. This guide will walk you through the key components of the platform and help you understand how to use and extend it effectively.

## Prerequisites

Before you begin, ensure you have:

- Docker and Docker Compose installed
- Basic knowledge of Python and Django
- Familiarity with REST API concepts
- Git for version control

## Setting Up Your Environment

SentinelIQ is designed to run in a containerized environment using Docker. To get started:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/sentineliq.git
   cd sentineliq
   ```

2. Start the Docker environment:
   ```bash
   docker-compose up -d
   ```

3. Run migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. Access the application:
   - API: http://localhost:8000/api/v1/
   - Admin: http://localhost:8000/admin/
   - Documentation: http://localhost:8000/api/docs/

## Project Structure Overview

SentinelIQ follows a modular architecture with clear separation of concerns:

```
project_root/
├── api/
│   ├── core/           # Core components used across the platform
│   └── v1/             # API version 1 endpoints and apps
├── audit_logs/         # Centralized audit logging system
├── tests/              # Centralized test suite
├── logs/               # Application logs
└── pyproject.toml      # Poetry dependency management
```

## Key Components

The following components form the foundation of SentinelIQ:

1. **Core API Framework** (`api.core`)
   - Response handling
   - RBAC implementation
   - Exception management
   - Pagination and filtering

2. **Audit Logging** (`audit_logs`)
   - Comprehensive activity tracking
   - Tenant isolation
   - Security monitoring

3. **Feature Modules**
   - Alerts
   - Incidents
   - Tasks
   - Reports
   - Users and Companies

## What You'll Learn

This tutorial will guide you through:

1. [Understanding the modular architecture](modular-architecture)
2. [Working with core components](core-components)
3. [Implementing standard API responses](response-handling)
4. [Setting up RBAC for security](rbac-basics)
5. [Handling errors properly](error-handling)
6. [Implementing audit logging](audit-logging)

## Development Philosophy

SentinelIQ adheres to strict enterprise-grade standards:

- **Modular Design** - Each component has a clear responsibility
- **Consistent Interfaces** - Standard patterns across all modules
- **Comprehensive Testing** - All code is thoroughly tested
- **Complete Documentation** - All components are fully documented
- **Security First** - RBAC and audit logging are fundamental

In the next section, we'll explore the [modular architecture](modular-architecture) in detail. 