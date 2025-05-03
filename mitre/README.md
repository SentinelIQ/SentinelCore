# MITRE ATT&CK Framework Integration

This module provides integration with the MITRE ATT&CK Framework, allowing mapping of tactics, techniques, and procedures (TTPs) to alerts, incidents, and observables in the Sentineliq platform.

## Features

- Local database of MITRE ATT&CK data (tactics, techniques, mitigations, relationships)
- Automatic synchronization with the latest MITRE ATT&CK data (every 10 minutes)
- Mapping of alerts/incidents/observables to MITRE techniques
- Automatic tagging based on pattern recognition (via SentinelVision)
- Full RBAC and multi-tenant compliance
- Enrichment backend for SentinelVision modules

## Commands

### Import MITRE Data

```bash
docker compose exec web python manage.py import_mitre [--source json|taxii] [--url URL] [--force] [--no-relationships]
```

Options:
- `--source`: Source type (json or taxii, default: json)
- `--url`: Custom URL to fetch data from (optional)
- `--force`: Force reimport of all data even if already exists
- `--no-relationships`: Skip importing relationships

### Check MITRE Status

```bash
docker compose exec web python manage.py mitre_status [--detailed]
```

Options:
- `--detailed`: Show detailed statistics

## API Endpoints

All endpoints follow kebab-case convention and are available at `/api/v1/mitre/`.

### MITRE Framework Data

- `/api/v1/mitre/tactics/` - List all MITRE tactics
- `/api/v1/mitre/techniques/` - List all MITRE techniques
- `/api/v1/mitre/mitigations/` - List all MITRE mitigations
- `/api/v1/mitre/relationships/` - List all MITRE relationships

### Mappings

- `/api/v1/mitre/alert-mappings/` - Map alerts to MITRE techniques
- `/api/v1/mitre/incident-mappings/` - Map incidents to MITRE techniques
- `/api/v1/mitre/observable-mappings/` - Map observables to MITRE techniques

## Celery Tasks

The module includes a Celery task that runs every 10 minutes to sync with the latest MITRE ATT&CK data:

```python
from mitre.tasks import sync_mitre_data

# Run manually if needed
sync_mitre_data.delay()
```

## Integration Points

This module integrates with:

- **Alerts**: Map indicators to techniques via enrichment
- **Incidents**: Analysts manually tag tactics/techniques
- **Observables**: Auto-mapping through SentinelVision analyzers
- **Dashboard**: Breakdown of cases by TTP or kill chain phase
- **Reporting**: Include MITRE references per incident report

## Permissions

- Superusers (`adminsentinel`) can perform updates or imports
- All users can access MITRE-mapped data via DRF endpoints
- Standard RBAC inheritance from the mapped entity (alert/incident/observable) 