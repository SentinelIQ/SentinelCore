    # SentinelVision Integration

This guide explains how to integrate SentinelIQ with SentinelVision for enhanced security monitoring and incident response.

## Overview

SentinelVision integration provides:
- Real-time security event monitoring
- Advanced threat detection
- Automated incident creation
- Unified security dashboard
- Correlated threat intelligence

## Prerequisites

1. SentinelIQ instance running and configured
2. SentinelVision instance running and configured
3. Network connectivity between both systems
4. API access credentials for both platforms

## Configuration Steps

### 1. Generate API Credentials

```bash
# Generate SentinelVision API key
sentinelvision-cli generate-api-key --name "sentineliq-integration"

# Store the API key securely
echo "SENTINELVISION_API_KEY=your_api_key" >> .env
```

### 2. Configure Integration

```python
# Configure SentinelVision integration in settings.py
SENTINELVISION_CONFIG = {
    'enabled': True,
    'api_url': 'https://vision.your-domain.com/api/v1',
    'api_key': os.getenv('SENTINELVISION_API_KEY'),
    'verify_ssl': True,
    'timeout': 30,
}

# Configure event forwarding
EVENT_FORWARDING = {
    'sentinelvision': {
        'enabled': True,
        'events': [
            'alert.created',
            'alert.updated',
            'incident.created',
            'incident.updated',
        ],
    },
}
```

### 3. Enable Data Collection

```bash
# Configure data collection
docker compose exec web python manage.py configure_sentinelvision

# Test connection
docker compose exec web python manage.py test_sentinelvision
```

## Integration Features

### 1. Event Forwarding

SentinelIQ automatically forwards security events to SentinelVision:
- Alert creation and updates
- Incident creation and updates
- Task status changes
- System events

### 2. Threat Intelligence

SentinelVision provides enhanced threat intelligence:
- Real-time threat detection
- Behavioral analysis
- Anomaly detection
- Correlation analysis

### 3. Unified Dashboard

Access SentinelVision data directly in SentinelIQ:
- Security events overview
- Threat intelligence feed
- Incident correlation
- Performance metrics

## API Integration

### 1. Event API

```python
from sentineliq.integrations import SentinelVision

# Initialize integration
vision = SentinelVision()

# Forward event
vision.forward_event({
    'type': 'alert.created',
    'data': {
        'alert_id': 'ALT-123',
        'title': 'Suspicious Activity Detected',
        'severity': 'high',
    },
})
```

### 2. Query API

```python
# Query SentinelVision data
events = vision.query_events(
    start_time='2024-03-15T00:00:00Z',
    end_time='2024-03-15T23:59:59Z',
    event_type='alert',
)

# Process results
for event in events:
    process_event(event)
```

## Troubleshooting

### 1. Connection Issues

```bash
# Check connectivity
docker compose exec web python manage.py check_sentinelvision_connection

# View logs
docker compose exec web python manage.py view_sentinelvision_logs
```

### 2. Data Sync Issues

```bash
# Check sync status
docker compose exec web python manage.py check_sentinelvision_sync

# Force sync
docker compose exec web python manage.py force_sentinelvision_sync
```

## Best Practices

1. **Event Forwarding**
   - Forward relevant events only
   - Configure appropriate filters
   - Monitor event queue
   - Handle failures gracefully

2. **Data Management**
   - Regular data cleanup
   - Optimize storage
   - Monitor performance
   - Backup configuration

3. **Security**
   - Secure API credentials
   - Use SSL/TLS
   - Regular access review
   - Audit logging

## Next Steps

1. Configure [Event Forwarding](../configuration/connectors.md)
2. Set up [Dashboards](../user-guides/dashboards.md)
3. Review [Security Operations](../operations/security.md)

## Support

For integration support:

- Email: support@sentineliq.com
- Documentation: [API Documentation](../api/documentation.md)
- Community: [GitHub Discussions](https://github.com/sentineliq/sentineliq/discussions) 