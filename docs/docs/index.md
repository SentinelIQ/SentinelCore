---
sidebar_position: 1
slug: /
---

# SentinelIQ - Enterprise-grade Security Platform

SentinelIQ is an enterprise-grade security platform built with Django REST Framework, providing robust security monitoring, incident management, and compliance features.

## Overview

SentinelIQ delivers a comprehensive security solution with emphasis on:

- **Role-Based Access Control (RBAC)** - Enterprise-grade permission system
- **Audit Logging** - Complete traceability of all system actions
- **Multi-tenant Architecture** - Secure isolation between organizations
- **Modular Structure** - Clean, maintainable codebase architecture
- **Docker-based Deployment** - Containerized for consistency and scalability

## Core Features

- **Security Alerts Management** - Real-time monitoring and alerting
- **Incident Response** - Structured workflows for security incidents
- **Compliance Reporting** - Automated compliance documentation
- **User & Company Management** - Complete identity management
- **Audit Trails** - Comprehensive action logging across the system

## Architecture

SentinelIQ follows a modular architecture with clear separation of concerns:

```
project_root/
├── api/
│   └── v1/
│       └── <modular_apps>/
├── tests/
│   ├── alerts/
│   ├── incidents/
│   └── ...
├── logs/
├── docs/
├── pyproject.toml  ← Poetry only
└── ...
```

Each module is structured to maintain enterprise-grade quality standards:

```
<app>/
├── views/
│   ├── __init__.py                ← combines view mixins
│   ├── <resource>_create.py
│   ├── <resource>_detail.py
│   └── <resource>_custom_actions.py
├── serializers/
├── permissions/
├── filters/
```

## Getting Started

- [Features Overview](features)
- [Learn SentinelIQ](learn/index)
- [Tutorials](tutorial/intro)
- [API Reference](reference/api-core) 