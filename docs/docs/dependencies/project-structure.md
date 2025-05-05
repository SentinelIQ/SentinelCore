---
sidebar_position: 3
---

# Project Structure

SentinelIQ follows a well-defined project structure to ensure maintainability and scalability.

## Directory Structure

The top-level structure of the project is organized as follows:

```
project_root/
├── api/
│   ├── core/           # Core framework components
│   └── v1/             # API version 1
│       ├── alerts/     # Alert management
│       ├── incidents/  # Incident management
│       ├── tasks/      # Task management
│       └── ...
├── audit_logs/         # Centralized audit logging
├── tests/              # Centralized test directory
│   ├── alerts/
│   ├── incidents/
│   └── ...
├── logs/               # Application logs
│   ├── api.log
│   ├── error.log
│   └── django.log
├── docs/               # Documentation
├── pyproject.toml      # Poetry dependency management
├── docker-compose.yml  # Docker Compose configuration
└── Dockerfile          # Docker image definition
```

## App Structure

Each app follows a modular structure:

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
│   └── detail.py            # Detail-specific serializers
├── models/
│   ├── __init__.py
│   └── resource.py          # Resource models
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

## Core Components

The `api.core` module contains common components used across the platform:

```
api/core/
├── responses.py         # API response formatting
├── rbac.py              # Role-based access control
├── permissions.py       # Common permission classes
├── exceptions.py        # Exception handling
├── pagination.py        # Pagination classes
├── filters.py           # Filter utilities
├── middleware.py        # Request/response middleware
├── audit.py             # Audit logging integration
├── viewsets.py          # Base viewset classes
└── utils.py             # Utility functions
```

## Test Organization

Unlike standard Django apps, tests are centralized in a `/tests/` directory:

```
tests/
├── alerts/
│   ├── test_alert_create.py
│   ├── test_alert_update.py
│   └── test_alert_actions.py
├── incidents/
│   ├── test_incident_create.py
│   └── ...
└── ...
```

## Log Organization

Logs are organized by type:

```
logs/
├── api.log       # API request/response logs
├── error.log     # Error logs
└── django.log    # Django framework logs
```

## Best Practices

1. **Modular Organization** - Keep functionality cleanly separated
2. **Clear Responsibilities** - Each module should have a single responsibility
3. **Consistent Naming** - Follow naming conventions across the codebase
4. **Documentation** - Keep documentation in sync with code changes
5. **Test Coverage** - Ensure all components have corresponding tests

## Development Flow

When extending the project, follow these steps:

1. Create new apps using the `startapp` command
2. Organize the app following the modular structure
3. Register the app in `settings.py`
4. Add URL routes in `urls.py`
5. Create tests in the `/tests/` directory
6. Register models for audit logging 