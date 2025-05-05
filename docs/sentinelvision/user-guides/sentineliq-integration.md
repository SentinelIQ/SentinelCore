# SentinelIQ Integration

This guide explains how to integrate SentinelVision with SentinelIQ for comprehensive security incident management.

## Overview

SentinelIQ integration enables:
- Automated incident creation
- Bi-directional event synchronization
- Unified threat management
- Automated response actions
- Integrated reporting

## Prerequisites

1. SentinelVision instance running and configured
2. SentinelIQ instance running and configured
3. Network connectivity between both systems
4. API access credentials for both platforms

## Configuration Steps

### 1. Generate API Credentials

```bash
# Generate SentinelIQ API key
sentineliq-cli generate-api-key --name "sentinelvision-integration"

# Store the API key securely
echo "SENTINELIQ_API_KEY=your_api_key" >> .env
```

### 2. Configure Integration

```python
# Configure SentinelIQ integration in settings.py
SENTINELIQ_CONFIG = {
    'enabled': True,
    'api_url': 'https://iq.your-domain.com/api/v1',
    'api_key': os.getenv('SENTINELIQ_API_KEY'),
    'verify_ssl': True,
    'timeout': 30,
}

# Configure event synchronization
EVENT_SYNC = {
    'sentineliq': {
        'enabled': True,
        'events': [
            'threat.detected',
            'anomaly.detected',
            'incident.detected',
            'alert.generated',
        ],
        'thresholds': {
            'severity': 'medium',
            'confidence': 0.7,
        },
    },
}
```

### 3. Enable Integration

```bash
# Configure integration
docker compose exec web python manage.py configure_sentineliq

# Test connection
docker compose exec web python manage.py test_sentineliq
```

## Integration Features

### 1. Event Synchronization

SentinelVision automatically forwards relevant events to SentinelIQ:
- Detected threats
- Security anomalies
- System alerts
- Compliance violations

### 2. Incident Management

Automatic incident creation in SentinelIQ based on:
- Severity thresholds
- Event correlation
- Threat intelligence
- Custom rules

### 3. Data Enrichment

Enhance SentinelIQ incidents with:
- Event timeline
- System metrics
- Network data
- Log analysis

## API Integration

### 1. Event API

```python
from sentinelvision.integrations import SentinelIQ

# Initialize integration
iq = SentinelIQ()

# Forward threat detection
iq.create_incident({
    'title': 'Advanced Persistent Threat Detected',
    'description': 'Suspicious network behavior indicating APT activity',
    'severity': 'high',
    'source': 'SentinelVision',
    'evidence': {
        'network_logs': ['...'],
        'system_metrics': {'...'},
        'timeline': ['...'],
    },
})
```

### 2. Query API

```python
# Query SentinelIQ incidents
incidents = iq.query_incidents(
    start_time='2024-03-15T00:00:00Z',
    end_time='2024-03-15T23:59:59Z',
    severity=['high', 'critical'],
)

# Process results
for incident in incidents:
    update_local_status(incident)
```

## Dashboards

### 1. Integration Dashboard

Configure the SentinelIQ integration dashboard:
- Event synchronization status
- Incident creation metrics
- Response time analytics
- Integration health

### 2. Custom Widgets

Create custom dashboard widgets:
- Incident distribution
- Severity trends
- Response metrics
- Integration status

## Troubleshooting

### 1. Connection Issues

```bash
# Check connectivity
docker compose exec web python manage.py check_sentineliq_connection

# View logs
docker compose exec web python manage.py view_sentineliq_logs
```

### 2. Sync Issues

```bash
# Check sync status
docker compose exec web python manage.py check_sentineliq_sync

# Force sync
docker compose exec web python manage.py force_sentineliq_sync
```

## Best Practices

1. **Event Management**
   - Configure appropriate thresholds
   - Filter relevant events
   - Monitor sync queue
   - Handle failures gracefully

2. **Performance**
   - Optimize event forwarding
   - Monitor resource usage
   - Regular maintenance
   - Cache management

3. **Security**
   - Secure API keys
   - Use SSL/TLS
   - Regular audits
   - Access control

## Next Steps

1. Configure [Data Sources](data-sources.md)
2. Set up [Custom Dashboards](dashboards.md)
3. Review [Reports](reports.md)

## Support

For integration support:

- Email: support@sentineliq.com
- Documentation: [API Documentation](../api/documentation.md)
- Community: [GitHub Discussions](https://github.com/sentineliq/sentineliq/discussions) 