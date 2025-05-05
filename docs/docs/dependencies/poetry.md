---
sidebar_position: 1
---

# Poetry Dependency Management

SentinelIQ uses Poetry exclusively for Python dependency management. This guide explains how to work with Poetry in the context of SentinelIQ's development environment.

## Overview

Poetry is a modern dependency management and packaging tool for Python that simplifies dependency management and environment creation. SentinelIQ strictly prohibits the use of `requirements.txt` files or direct `pip` installations to ensure consistent environments across development, testing, and production.

## Key Benefits

- **Dependency Resolution** - Automatically resolves dependencies and their versions
- **Reproducible Environments** - Ensures consistent environments across systems
- **Lock Files** - Locks dependency versions for predictable builds
- **Virtual Environments** - Automatically manages virtual environments
- **Build & Publishing** - Simplifies package building and publishing

## Setting Up

SentinelIQ's Docker-based environment already includes Poetry, so you don't need to install it separately.

## pyproject.toml

The `pyproject.toml` file is the central configuration file for Poetry. It defines the project's dependencies, development dependencies, Python version, and other metadata.

Example `pyproject.toml`:

```toml
[tool.poetry]
name = "sentineliq"
version = "3.0.0"
description = "Enterprise-grade security platform"
authors = ["SentinelIQ Team <dev@sentineliq.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
django = "^4.2.0"
djangorestframework = "^3.14.0"
psycopg2-binary = "^2.9.5"
celery = "^5.2.7"
redis = "^4.5.1"
pyjwt = "^2.6.0"
drf-spectacular = "^0.26.0"
django-cors-headers = "^3.14.0"
django-filter = "^23.1.0"
gunicorn = "^20.1.0"
uvicorn = "^0.22.0"
sentry-sdk = "^1.23.1"

[tool.poetry.group.dev.dependencies]
pytest = "^7.3.1"
pytest-django = "^4.5.2"
black = "^23.3.0"
isort = "^5.12.0"
mypy = "^1.2.0"
flake8 = "^6.0.0"
django-debug-toolbar = "^4.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

## Common Poetry Commands

### Adding Dependencies

To add a new dependency, always use Poetry inside the Docker container:

```bash
docker compose exec web poetry add <package-name>
```

For development dependencies:

```bash
docker compose exec web poetry add --group dev <package-name>
```

### Updating Dependencies

To update dependencies to their latest versions:

```bash
docker compose exec web poetry update
```

To update a specific package:

```bash
docker compose exec web poetry update <package-name>
```

### Installing Dependencies

When starting a fresh environment, Poetry automatically installs dependencies based on the lock file:

```bash
docker compose exec web poetry install
```

For production, exclude development dependencies:

```bash
docker compose exec web poetry install --without dev
```

### Viewing Dependencies

To see the current dependencies and their versions:

```bash
docker compose exec web poetry show
```

For a tree view of dependencies:

```bash
docker compose exec web poetry show --tree
```

### Exporting Dependencies

While SentinelIQ uses Poetry exclusively, you may sometimes need to export dependencies to a requirements format:

```bash
docker compose exec web poetry export -f requirements.txt --output requirements.txt
```

Including development dependencies:

```bash
docker compose exec web poetry export --with dev -f requirements.txt --output requirements-dev.txt
```

## Poetry Lock File

The `poetry.lock` file is automatically generated and updated by Poetry. It locks the exact versions of all dependencies and their sub-dependencies. This file should always be committed to version control to ensure all developers and environments use the exact same package versions.

## Best Practices

1. **Always Use the Container** - Run all Poetry commands inside the Docker container
2. **Keep Lock File Updated** - Commit the `poetry.lock` file to version control
3. **Group Dependencies** - Use Poetry's dependency groups to organize dependencies
4. **Be Specific with Versions** - Specify version constraints for all dependencies
5. **Regular Updates** - Regularly update dependencies to get security patches
6. **CI Integration** - Use Poetry in CI/CD pipelines for consistent builds

## Common Issues and Solutions

### Package Conflicts

If you encounter dependency conflicts:

```bash
docker compose exec web poetry update --lock
```

### Version Constraints

Use version constraints to specify compatible versions:

- `^1.2.3`: Compatible with &gt;=1.2.3 &lt;2.0.0
- `~1.2.3`: Compatible with &gt;=1.2.3 &lt;1.3.0
- `>=1.2.3`: Greater than or equal to 1.2.3
- `==1.2.3`: Exactly 1.2.3

### Virtual Environment

Poetry manages its own virtual environments. In the Docker container, the virtual environment is already activated, so you don't need to worry about activating it manually.

## Security Considerations

1. **Regular Updates** - Keep dependencies updated to address security vulnerabilities
2. **Audit** - Regularly audit dependencies for security issues
3. **Pin Versions** - Pin versions to prevent unexpected changes
4. **Minimize Dependencies** - Only add dependencies that are strictly necessary 