---
sidebar_position: 2
---

# Docker Setup

SentinelIQ is fully containerized using Docker, ensuring consistent development and deployment environments.

## Overview

Docker is used to create isolated, reproducible environments for development, testing, and production. SentinelIQ requires all commands to be executed within the Docker container to ensure consistency.

## Docker Compose Configuration

The project uses Docker Compose to define and run multi-container applications:

```yaml
version: '3.8'

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=1
      - DATABASE_URL=postgres://postgres:postgres@db:5432/sentineliq
      - REDIS_URL=redis://redis:6379/0
      
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=sentineliq
    ports:
      - "5432:5432"
      
  redis:
    image: redis:6
    ports:
      - "6379:6379"
      
  celery:
    build: .
    command: celery -A sentineliq worker -l info
    volumes:
      - .:/app
    depends_on:
      - web
      - redis
    environment:
      - DEBUG=1
      - DATABASE_URL=postgres://postgres:postgres@db:5432/sentineliq
      - REDIS_URL=redis://redis:6379/0

volumes:
  postgres_data:
```

## Development Workflow

All development commands should be run inside the Docker container:

```bash
# Start the environment
docker-compose up -d

# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Add dependencies
docker-compose exec web poetry add <package-name>

# Run tests
docker-compose exec web python manage.py test tests

# Access the shell
docker-compose exec web python manage.py shell
```

## Best Practices

1. **Always Use the Container** - Never run commands directly on the host
2. **Volume Mounting** - Use volume mounts for development to reflect changes immediately
3. **Environment Variables** - Use environment variables for configuration
4. **Container Isolation** - Keep services isolated in their own containers
5. **Persistent Data** - Use named volumes for persistent data

## Common Issues and Solutions

[Content to be added in future updates]

## Production Considerations

[Content to be added in future updates] 