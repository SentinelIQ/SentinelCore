# SentinelIQ Role-Based Access Control (RBAC) System

This document explains the RBAC system implemented in SentinelIQ. The system provides granular control over what actions users can perform based on their role and company.

## Role Definitions

SentinelIQ implements a hierarchical role system with the following roles:

### Global Role (Platform Scope)

| Role      | Scope   | Description                          |
|-----------|---------|--------------------------------------|
| `superuser`| Global  | Superadmin with full unrestricted access |

### Per-Company Roles (Organization Scope)

| Role             | Scope     | Description                                 |
|------------------|-----------|---------------------------------------------|
| `admin_company`  | Per-Tenant| Admin for a company; manage all internal data |
| `analyst_company`| Per-Tenant| Analyst with create/update/read permissions |
| `read_only`      | Per-Tenant| Analyst with read-only access               |

## Permission Matrix

The RBAC system is based on a central permission matrix that maps roles to permissions. This matrix is defined in `auth_app/permission_matrix.py`.

Each role is assigned a set of permissions that determine what actions the user can perform. Permissions follow a naming convention: `<action>_<entity>`.

For example:
- `view_alert`: Permission to view alerts
- `create_incident`: Permission to create incidents
- `manage_users`: Permission to manage users (includes create, update, delete)

## Entity Types and Actions

The following entities are governed by the RBAC system:

- `company`: Companies (tenants)
- `user`: Users and authentication
- `alert`: Security alerts
- `incident`: Security incidents (cases)
- `task`: Tasks within incidents
- `observable`: Observables within alerts/incidents
- `wiki`: Knowledge base articles
- `report`: Generated reports
- `dashboard`: Dashboards and metrics
- `notification`: User notifications
- `misp`: MISP integration
- `mitre`: MITRE ATT&CK integration
- `analyzers`: SentinelVision analyzers
- `responders`: SentinelVision automated responders

## How Permissions are Enforced

The RBAC system enforces permissions at two levels:

1. **View-Level Permissions**: Determines if a user can access a view (endpoint) based on their role and the required permission for that view.

2. **Object-Level Permissions**: Determines if a user can access a specific object based on their role, permissions, and tenant isolation (company membership).

The system automatically maps HTTP methods to permission prefixes:
- GET → view
- POST → create
- PUT/PATCH → update
- DELETE → delete

## Implementation Details

### HasEntityPermission

The core of the RBAC system is the `HasEntityPermission` class in `api/core/rbac.py`. This class:

1. Determines the entity type and required permission from the view and HTTP method
2. Checks if the user's role has the required permission
3. Enforces tenant isolation by ensuring users can only access objects in their company

### Entity-Specific Permissions

Each app has its own permission class that extends `HasEntityPermission`, allowing for customization of permission logic specific to that entity.

### ViewSet Integration

ViewSets use the permission classes and define their `entity_type` to integrate with the RBAC system:

```python
class AlertViewSet(viewsets.ModelViewSet):
    permission_classes = [AlertPermission]
    entity_type = 'alert'
    # ... other ViewSet configuration
```

## Tenant Isolation

The RBAC system enforces strict tenant isolation:
- Superusers can access data across all companies
- Company users can only access data within their own company
- Object-level permissions ensure users cannot access objects from other companies

## Validation and Maintenance

Use the management command to validate the RBAC setup:

```bash
python manage.py validate_rbac
```

This command checks for:
- Missing roles in the permission matrix
- ViewSets missing entity_type
- Permission hierarchy consistency

## Permission Table

| Entity / Action                | superuser | admin_company | analyst_company | read_only |
|-------------------------------|-----------|---------------|-----------------|-----------|
| View dashboards               | ✅        | ✅             | ✅              | ✅        |
| Manage users                  | ✅        | ✅             | ❌              | ❌        |
| Create/update/delete alerts   | ✅        | ✅             | ✅              | ❌        |
| View alerts                   | ✅        | ✅             | ✅              | ✅        |
| Create/update/delete incidents| ✅        | ✅             | ✅              | ❌        |
| View incidents                | ✅        | ✅             | ✅              | ✅        |
| Manage tasks                  | ✅        | ✅             | ✅              | ❌        |
| Run responders                | ✅        | ✅             | ✅              | ❌        |
| Run analyzers                 | ✅        | ✅             | ❌              | ❌        |
| Manage notifications          | ✅        | ✅             | ❌              | ❌        |
| Generate case reports         | ✅        | ✅             | ✅              | ❌        |
| Manage wiki/articles          | ✅        | ✅             | ✅              | ❌        | 