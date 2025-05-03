# Sentry Integration in SentinelIQ

This document describes how Sentry is integrated with SentinelIQ for error monitoring and performance tracking in production.

## Overview

Sentry is an error monitoring and performance platform that allows us to:

- Monitor errors in real-time across all environments
- Record performance information (APM)
- Create code profiles to identify bottlenecks
- Track transactions to understand request flows
- Associate errors with specific application versions

## Configuration

Sentry integration is handled through the `sentineliq/sentry.py` file and is automatically initialized during application startup in `sentineliq/__init__.py`.

### Environment Variables

The following environment variables can be used to configure Sentry:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| SENTRY_DSN | Sentry project DSN URL | https://3a46c79a44b25a0942956e683f4d6c22@o4508786411307008.ingest.us.sentry.io/4509251376185344 |
| SENTRY_RELEASE | Application version | Git commit hash |
| SENTRY_SAMPLE_RATE | General sampling rate | 1.0 (100%) |
| SENTRY_TRACES_SAMPLE_RATE | Transaction sampling rate | 1.0 (100%) |
| SENTRY_PROFILES_SAMPLE_RATE | Profile sampling rate | 1.0 (100%) |
| ENVIRONMENT | Application environment | development |

## Usage in Application

### User Context

The `SentryContextMiddleware` automatically adds user and request information to Sentry events.

### Capturing Errors

Unhandled errors are automatically captured by Sentry. To capture specific messages or errors:

```python
from sentineliq.sentry import capture_message

# Capture an informational message
capture_message("Operation completed successfully", level="info")

# Capture an error
try:
    # code that might fail
except Exception as e:
    capture_message(f"Error while processing: {str(e)}", level="error")
    raise
```

### Adding Context

To add additional context to events:

```python
from sentineliq.sentry import set_context, set_user, set_transaction

# Set user information
set_user({
    'id': user.id,
    'email': user.email,
    'username': user.username
})

# Add custom context
set_context("operation_details", {
    "account_id": account.id,
    "operation_type": "transfer",
    "amount": amount
})

# Set transaction name
set_transaction("process_payment")
```

### Utilities for Background Services

For background services (Celery, scripts, etc.), use the decorators in `api.core.utils.sentry_utils`:

```python
from api.core.utils.sentry_utils import with_sentry_context, capture_errors

# Add context to a function
@with_sentry_context("user_service")
def process_user_data(user_id):
    # function code

# Automatically capture errors
@capture_errors("payment_service", reraise=True)
def process_payment(payment_id):
    # code that might raise exceptions
```

## Testing the Integration

### Test Endpoint

An endpoint to test the integration is available at `/api/v1/common/test-sentry/`. This endpoint requires authentication and admin permissions.

#### Parameters

- `debug=true` - Causes a deliberate error to test exception capturing
- `celery=true` - Executes a Celery task that will generate an error to test Celery integration

### Celery Test Task

The `test_sentry_task` in `sentineliq/celery.py` can be used to test Celery integration:

```python
from sentineliq.celery import test_sentry_task

# Execute the task that will cause an error
result = test_sentry_task.delay()
```

## Dashboards and Alerts

In Sentry, we have the following dashboards and alerts configured:

1. **Critical Errors** - Immediately notifies the on-call team about critical errors in production
2. **Performance** - Monitors response times and identifies slow endpoints
3. **Errors by Release** - Tracks the quality of each release
4. **Most Frequent Errors** - Lists the most common errors for prioritization

## Best Practices

1. **Don't include sensitive information** - Never include passwords, tokens, or sensitive personal data in events
2. **Use tags for filtering** - Add tags to events to facilitate filtering
3. **Descriptive transaction names** - Use names that clearly identify what's being executed
4. **Add breadcrumbs** - For complex operations, add breadcrumbs to help understand the flow

## Troubleshooting

If events aren't appearing in Sentry:

1. Verify that the DSN is correctly configured
2. Confirm that the integration is enabled by checking the initialization logs
3. Test using the `/api/v1/common/test-sentry/` endpoint
4. Check if any firewall is blocking requests to the Sentry domain 