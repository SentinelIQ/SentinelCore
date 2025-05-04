# Sentineliq API Tag Structure

This document outlines the OpenAPI/Swagger tag structure used in Sentineliq's API documentation, following Domain-Driven Design (DDD) principles.

## Domain-Driven Design Organization

Our API is organized around clear business domains rather than technical implementation details. This makes the API more intuitive for security professionals and helps separate concerns in our codebase.

## Enterprise-Grade Tag Structure

The following tags represent our functional domains:

| Domain | Description | Example Endpoints |
|--------|-------------|------------------|
| **Authentication & Access Control** | Endpoints for user login, JWT token handling, and RBAC access policies. | `/api/v1/auth/token/`, `/api/v1/auth/users/` |
| **Company Management** | Multi-tenant company provisioning, configuration, and statistics. | `/api/v1/companies/`, `/api/v1/companies/{id}/statistics/` |
| **Alert Management** | Security alert lifecycle including creation, triage, classification, and correlation. | `/api/v1/alerts/`, `/api/v1/alerts/{id}/escalate/` |
| **Incident Management** | Case and incident tracking with escalation, investigation, and resolution workflow. | `/api/v1/incidents/`, `/api/v1/incidents/{id}/timeline/` |
| **Observables & IOCs** | Submission, enrichment, tagging, and search of indicators of compromise. | `/api/v1/observables/`, `/api/v1/observables/{id}/enrich/` |
| **Threat Intelligence (SentinelVision)** | Analyzer modules, threat feeds, and automated responders for enrichment and action. | `/api/v1/sentinel-vision/analyzers/`, `/api/v1/sentinel-vision/feeds/` |
| **Notification System** | Notification rules, delivery methods (e-mail, Slack, webhook), and logs. | `/api/v1/notifications/`, `/api/v1/notifications/channels/` |
| **Knowledge Base (Wiki)** | Internal documentation including runbooks, categories, and standard procedures. | `/api/v1/wiki/articles/`, `/api/v1/wiki/categories/` |
| **Reporting** | Report generation in Markdown or PDF format for audit and evidence purposes. | `/api/v1/reporting/templates/`, `/api/v1/reporting/generate/` |
| **System Monitoring & Operations** | Health checks, logs, background tasks, and platform-level diagnostics. | `/api/v1/system/health/`, `/api/v1/system/tasks/` |
| **Task Management** | Assignment and tracking of security tasks and playbook execution. | `/api/v1/tasks/`, `/api/v1/tasks/{id}/assign/` |
| **MITRE Framework** | MITRE ATT&CK framework mapping and threat intelligence correlation. | `/api/v1/mitre/techniques/`, `/api/v1/mitre/mappings/` |

## Global vs. Tenant-Scoped Endpoints

Within each domain, endpoints are categorized as:

- **Global endpoints**: Platform-wide operations available to superusers
- **Tenant-scoped endpoints**: Operations limited to a specific company/tenant

This distinction is noted in the endpoint descriptions and enforced through RBAC policies.

## Tag Implementation

Tags are applied consistently using DRF Spectacular's `@extend_schema` and `@extend_schema_view` decorators:

```python
# For viewsets
@extend_schema_view(
    list=extend_schema(tags=['Alert Management']),
    retrieve=extend_schema(tags=['Alert Management']),
    # ... other actions
)
class AlertViewSet(StandardViewSet):
    pass

# For function-based views
@extend_schema(tags=['Authentication & Access Control'])
@api_view(['POST'])
def some_view(request):
    pass
```

## Benefits of This Structure

1. **Clear organization**: Endpoints are grouped by business function, not technical implementation
2. **Consistent naming**: Professional, enterprise-grade tag names
3. **Better developer experience**: Easier to find related endpoints
4. **Documentation clarity**: Each tag has a clear, concise description

## Maintenance

When adding new endpoints, assign them to the appropriate domain tag. If you need to create a new domain, update:

1. The `SPECTACULAR_SETTINGS['TAGS']` list in `settings.py`
2. This documentation file
3. Ensure all related views use the new tag 