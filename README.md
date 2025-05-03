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