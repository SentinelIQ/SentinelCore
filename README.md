# Sentineliq

A secure, scalable B2B Django REST API for managing companies and their users.

## Features

- Token-based authentication with JWT
- Role-based access control (Superuser, Admin Company, Analyst Company)
- Company data isolation (each company manages only its own data)
- RESTful API with versioning
- Comprehensive logging and error handling
- Containerized development environment with Docker and Docker Compose
- Flexible notification engine with multiple delivery channels (Email, Slack, Webhook)
- Metrics and dashboards for operational intelligence with KPIs
- SOAR/SIEM capabilities for alert and incident management

## Tech Stack

- Python 3.13
- Django 5.0+
- Django REST Framework 3.15+
- PostgreSQL 15+
- Poetry for dependency management
- Docker and Docker Compose for containerization
- Celery for async tasks and notifications

## Project Structure

```
sentineliq/
├── api/                  # API configuration
├── alerts/               # Alert management
├── auth_app/             # Authentication and user management
├── companies/            # Company-related models and logic
├── dashboard/            # Metrics and dashboards
├── incidents/            # Incident management
├── logs/                 # Application logs
├── notifications/        # Notification engine
├── reporting/            # Report generation
├── sentineliq/           # Project settings
├── tasks/                # Task management
├── tests/                # Centralized tests
├── .env                  # Environment variables
├── .env.example          # Example environment variables
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker configuration
├── pyproject.toml        # Poetry dependency management
└── README.md             # Project documentation
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Poetry 2.0+

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd sentineliq
```

2. Create a `.env` file based on the `.env.example`:

```bash
cp .env.example .env
```

3. Build and start the containers with Docker Compose:

```bash
docker compose up -d
```

4. Create initial migration files for the database models:

```bash
docker compose exec web python manage.py makemigrations auth_app companies
```

5. Apply database migrations:

```bash
docker compose exec web python manage.py migrate
```

The application will automatically create a superuser with the credentials specified in the `.env` file.

6. Verify the application is running:

```bash
# Check logs
docker compose logs -f web

# Access the application
# - API: http://localhost:8000/api/v1/
# - Admin interface: http://localhost:8000/admin/
```

## API Endpoints

### Authentication

- `POST /api/v1/token/` - Obtain JWT token pair
- `POST /api/v1/token/refresh/` - Refresh JWT token

### User Management

- `GET /api/v1/users/` - List users (filtered by company for non-superusers)
- `POST /api/v1/users/` - Create a new user (superuser or admin company only)
- `GET /api/v1/users/<id>/` - Retrieve a specific user
- `PUT/PATCH /api/v1/users/<id>/` - Update a user
- `DELETE /api/v1/users/<id>/` - Delete a user
- `GET /api/v1/users/me/` - Get current user profile

### Companies

- `GET /api/v1/companies/` - List companies (filtered by user's company for non-superusers)
- `POST /api/v1/companies/` - Create a new company (superuser only)
- `GET /api/v1/companies/<id>/` - Retrieve a specific company
- `PUT/PATCH /api/v1/companies/<id>/` - Update a company (superuser only)
- `DELETE /api/v1/companies/<id>/` - Delete a company (superuser only)

### Notifications

- `GET /api/v1/notifications/` - List notifications
- `POST /api/v1/notifications/` - Create a notification
- `GET /api/v1/notifications/<id>/` - Retrieve a specific notification
- `PUT/PATCH /api/v1/notifications/<id>/` - Update a notification
- `DELETE /api/v1/notifications/<id>/` - Delete a notification
- `GET /api/v1/notifications/channels/` - List notification channels
- `POST /api/v1/notifications/channels/` - Create a notification channel
- `GET /api/v1/notifications/preferences/<user_id>/` - Get user notification preferences
- `PATCH /api/v1/notifications/preferences/<user_id>/` - Update user notification preferences
- `POST /api/v1/notifications/test/` - Test a notification channel

### Dashboard & Metrics

- `GET /api/v1/dashboard/summary/` - Get high-level dashboard metrics
- `GET /api/v1/dashboard/incidents/trends/` - Get incident trends and metrics
- `GET /api/v1/dashboard/alerts/severity/` - Get alert breakdown by severity
- `GET /api/v1/dashboard/custom/` - Dynamic metrics based on filters
- `GET /api/v1/dashboard/preferences/` - Get dashboard preferences
- `PUT /api/v1/dashboard/preferences/` - Update dashboard preferences

## Example API Calls

### Obtaining a JWT Token

```bash
curl -X POST http://localhost:8000/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"adminsentinel", "password":"change-me-in-production"}'
```

Response:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Creating a Company (Superuser Only)

```bash
curl -X POST http://localhost:8000/api/v1/companies/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"name": "New Company"}'
```

### Managing Users (Admin Company)

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "username": "new_analyst",
    "email": "analyst@company.com",
    "password": "secure_password",
    "role": "analyst_company",
    "first_name": "New",
    "last_name": "Analyst"
  }'
```

### Getting Dashboard Summary

```bash
curl -X GET http://localhost:8000/api/v1/dashboard/summary/ \
  -H "Authorization: Bearer <access_token>"
```

### Configuring a Notification Channel

```bash
curl -X POST http://localhost:8000/api/v1/notifications/channels/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "name": "Company Slack",
    "channel_type": "slack",
    "config": {
      "webhook_url": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
      "username": "SentinelIQ Bot",
      "icon_emoji": ":alert:"
    },
    "is_enabled": true
  }'
```

## Running Tests

```bash
docker compose exec web python manage.py test tests
```

## Development With Poetry

If you're developing without Docker, you can use Poetry directly:

```bash
# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Create and apply migrations
python manage.py makemigrations auth_app companies
python manage.py migrate

# Run the development server
python manage.py runserver

# Run tests
python manage.py test tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# SentinelIQ Audit Logging System

This document provides an overview of the centralized audit logging system implemented in SentinelIQ.

## Overview

The audit logging system captures and stores all critical operations performed in the SentinelIQ platform, including user actions, system operations, and background tasks. It provides a complete audit trail for compliance, security, and troubleshooting purposes.

## Key Features

- **Multi-tenant isolation**: All audit logs are isolated by company/tenant
- **Comprehensive coverage**: Logs all CRUD operations and custom actions
- **User tracking**: Records who performed each action
- **Detailed metadata**: Captures timestamps, IP addresses, HTTP methods, etc.
- **Background task logging**: Tracks Celery task execution
- **Sensitive data handling**: Automatically sanitizes passwords and tokens
- **Export capabilities**: Export logs to CSV, JSON, or Excel
- **Filtering and search**: Advanced filtering by entity type, action, date range, etc.

## Implementation Methods

There are several ways to integrate audit logging in SentinelIQ:

### 1. ViewSet Integration

For Django REST Framework ViewSets, use the `AuditLogMixin`:

```python
from api.core.audit import AuditLogMixin

class AlertViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """API endpoints for alerts."""
    entity_type = 'alert'
    # Other ViewSet configuration...
```

### 2. Custom Action Decorator

For custom ViewSet actions, use the `@audit_action` decorator:

```python
from api.core.audit import audit_action

@action(detail=True, methods=['post'])
@audit_action(action='escalate', entity_type='alert')
def escalate(self, request, pk=None):
    # Implementation...
```

### 3. Model Signal Integration

Model changes are automatically audited via Django signals. No additional code is required.

### 4. Celery Task Integration

For Celery tasks, use the `@audit_task` decorator or extend `AuditedTask`:

```python
from api.core.audit import audit_task

@app.task
@audit_task(entity_type='alert', get_entity_id=lambda alert_id, **kwargs: alert_id)
def process_alert(alert_id, **kwargs):
    # Task implementation...
```

### 5. Manual Logging

For custom code or more granular control:

```python
from auditlog.models import LogEntry

AuditLog.log_action(
    user=request.user,
    action='custom_action',
    entity_type='custom_entity',
    entity_id='123',
    entity_name='Custom Entity Name',
    request=request,
    company=company
)
```

## Accessing Audit Logs

- **API**: `/api/v1/audit-logs/` endpoints
- **Admin**: Django admin interface
- **Export**: `/api/v1/audit-logs/export/` endpoint

## Entity Types and Actions

See `api.v1.audit_logs.enums` for the full list of supported entity types and actions.

## Security Considerations

- Audit logs respect multi-tenant isolation
- Regular users can only see logs for their own company
- Passwords, tokens, and other sensitive data are automatically sanitized

## Best Practices

1. Always set the correct `entity_type` in ViewSets
2. Use explicit action names that describe what's happening
3. For custom actions, use the `@audit_action` decorator
4. Don't include sensitive data in log messages
5. Consider audit log volume when designing operations that might generate many logs

## Troubleshooting

If audit logs are not being created:

1. Check that the entity_type is set correctly
2. Verify that the `audit_logs` app is in `INSTALLED_APPS`
3. Check the Django logs for any errors in the audit logging process

## Documentation

SentinelIQ comes with comprehensive documentation built with MkDocs. 

To access the documentation:

1. Start the documentation server:
```bash
docker compose up sentineliq-docs -d
```

2. Access the documentation at http://localhost:8002

### Building Documentation

The documentation is automatically built and served by the `sentineliq-docs` service.

If you want to build the documentation manually:

```bash
docker compose exec sentineliq-docs mkdocs build
```

### Contributing to Documentation

Documentation source files are located in the `docs/` directory and are written in Markdown.

To add new documentation:

1. Create or edit files in the `docs/` directory
2. Update the navigation structure in `mkdocs.yml` if needed
3. The documentation server will automatically refresh with your changes

For more information on MkDocs, see the [MkDocs documentation](https://www.mkdocs.org/). 