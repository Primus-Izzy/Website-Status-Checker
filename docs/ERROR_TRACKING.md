# Error Tracking and Monitoring

This document describes the error tracking and monitoring system implemented in the Website Status Checker.

## Overview

The error tracking system provides:
- **Automatic error capture and categorization**
- **Error metrics collection** (counts, categories, severity)
- **Optional Sentry integration** for cloud-based error tracking
- **Custom error handlers** for specialized error processing
- **Thread-safe metrics collection**
- **FastAPI middleware** for HTTP request error tracking

## Components

### 1. Core Error Tracking (`src/utils/error_tracking.py`)

The core module provides:

#### ErrorCategory Enum
```python
class ErrorCategory(Enum):
    NETWORK = "network"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    FILE_IO = "file_io"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"
```

#### ErrorSeverity Enum
```python
class ErrorSeverity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

#### ErrorTracker Class
Main class for error tracking with methods:
- `capture_exception()` - Capture and track exceptions
- `capture_message()` - Capture non-exception messages
- `get_metrics()` - Retrieve error metrics
- `add_custom_handler()` - Add custom error processing

### 2. FastAPI Middleware (`gui/middleware/error_tracking.py`)

Automatically captures errors in HTTP requests and sends them to the error tracking system.

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Enable error tracking
ENABLE_ERROR_TRACKING=true

# Sentry DSN (optional, for cloud error tracking)
SENTRY_DSN=https://your-sentry-dsn-here@o123456.ingest.sentry.io/7654321

# Sentry environment name (defaults to ENV)
SENTRY_ENVIRONMENT=production

# Sentry sample rate (0.0 to 1.0)
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Python Configuration

In `gui/config.py`, the following settings are available:

```python
class Settings(BaseSettings):
    enable_error_tracking: bool = True
    sentry_dsn: str = ""
    sentry_environment: str = ""
    sentry_traces_sample_rate: float = 0.1
```

## Usage

### Basic Usage

#### Initialize Error Tracking

```python
from src.utils.error_tracking import initialize_error_tracking

# Without Sentry
tracker = initialize_error_tracking()

# With Sentry
tracker = initialize_error_tracking(
    enable_sentry=True,
    sentry_dsn="https://your-sentry-dsn@sentry.io/project",
    environment="production",
    release="1.0.0"
)
```

#### Capture Exceptions

```python
from src.utils.error_tracking import (
    get_error_tracker,
    ErrorCategory,
    ErrorSeverity
)

try:
    # Some operation that might fail
    result = risky_operation()
except Exception as exc:
    tracker = get_error_tracker()
    tracker.capture_exception(
        exc,
        context={
            "operation": "risky_operation",
            "user_id": "12345",
            "request_id": "abc-123"
        },
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        extra={
            "attempts": 3,
            "timeout": 30
        }
    )
```

#### Automatic Categorization

```python
from src.utils.error_tracking import categorize_exception, get_error_severity

try:
    # Operation
    pass
except Exception as exc:
    category = categorize_exception(exc)
    severity = get_error_severity(exc)

    tracker.capture_exception(exc, category=category, severity=severity)
```

### FastAPI Integration

#### Setup in main.py

```python
from fastapi import FastAPI
from gui.middleware.error_tracking import setup_error_tracking
from src.utils.error_tracking import initialize_error_tracking
from gui.config import get_settings

app = FastAPI()
settings = get_settings()

# Initialize error tracking
if settings.enable_error_tracking:
    initialize_error_tracking(
        enable_sentry=bool(settings.sentry_dsn),
        sentry_dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or settings.env,
        release=settings.app_version
    )

    # Add error tracking middleware
    setup_error_tracking(app)
```

### Custom Error Handlers

```python
def slack_notification_handler(exception: Exception, context: Dict[str, Any]):
    """Send critical errors to Slack."""
    if context.get("severity") == "critical":
        send_to_slack(f"Critical error: {exception}")

tracker = get_error_tracker()
tracker.add_custom_handler(slack_notification_handler)
```

### Error Metrics

#### Retrieve Metrics

```python
tracker = get_error_tracker()
metrics = tracker.get_metrics()

print(f"Total errors: {metrics['total_errors']}")
print(f"By category: {metrics['by_category']}")
print(f"By severity: {metrics['by_severity']}")
print(f"Unique types: {metrics['unique_error_types']}")
```

#### Example Metrics Output

```json
{
    "total_errors": 142,
    "by_type": {
        "ConnectionError": 45,
        "TimeoutError": 32,
        "ValueError": 15,
        "FileNotFoundError": 50
    },
    "by_category": {
        "network": 77,
        "validation": 15,
        "file_io": 50
    },
    "by_severity": {
        "error": 127,
        "warning": 15
    },
    "unique_error_types": 4,
    "first_seen": {
        "ConnectionError": "2025-01-15T10:23:45Z"
    },
    "last_seen": {
        "ConnectionError": "2025-01-15T14:52:31Z"
    }
}
```

## Sentry Integration

### Setup

1. **Create Sentry Account**
   - Sign up at https://sentry.io
   - Create a new project for your application

2. **Get DSN**
   - Navigate to Settings > Projects > Your Project > Client Keys (DSN)
   - Copy the DSN URL

3. **Configure Application**
   ```bash
   # .env
   SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
   SENTRY_ENVIRONMENT=production
   ```

4. **Install Sentry SDK** (optional)
   ```bash
   pip install sentry-sdk[fastapi]>=1.40.0
   ```

### Features

When Sentry is enabled, the following features are available:

- **Automatic error grouping** - Similar errors are grouped together
- **Release tracking** - Track errors by application version
- **Performance monitoring** - Track slow transactions
- **User context** - Associate errors with users
- **Breadcrumbs** - See events leading up to errors
- **Source maps** - Link errors to source code
- **Alerts** - Get notified of new errors

### Example Sentry Event

```python
tracker.capture_exception(
    ConnectionError("Failed to connect to database"),
    context={
        "database": "postgresql",
        "host": "db.example.com",
        "port": 5432
    },
    extra={
        "query": "SELECT * FROM users",
        "connection_pool_size": 10
    }
)
```

In Sentry, this appears as:
- **Issue Title**: ConnectionError: Failed to connect to database
- **Category**: network
- **Environment**: production
- **Tags**: error_category=network
- **Context**: Custom database connection info
- **Extras**: Query and pool size

## Best Practices

### 1. Use Appropriate Severity Levels

```python
# DEBUG: Development/diagnostic info
tracker.capture_exception(exc, severity=ErrorSeverity.DEBUG)

# WARNING: Potential issues that don't stop execution
tracker.capture_exception(exc, severity=ErrorSeverity.WARNING)

# ERROR: Failures that affect functionality
tracker.capture_exception(exc, severity=ErrorSeverity.ERROR)

# CRITICAL: System-threatening failures
tracker.capture_exception(exc, severity=ErrorSeverity.CRITICAL)
```

### 2. Add Contextual Information

```python
tracker.capture_exception(
    exc,
    context={
        "user_id": user.id,
        "request_id": request.id,
        "operation": "process_batch",
        "batch_size": 1000
    }
)
```

### 3. Categorize Errors Correctly

```python
# Network errors
tracker.capture_exception(exc, category=ErrorCategory.NETWORK)

# Validation errors
tracker.capture_exception(exc, category=ErrorCategory.VALIDATION)

# File I/O errors
tracker.capture_exception(exc, category=ErrorCategory.FILE_IO)
```

### 4. Use Custom Handlers for Alerts

```python
def critical_error_alert(exception: Exception, context: Dict):
    if context.get("severity") == ErrorSeverity.CRITICAL:
        send_pagerduty_alert(exception)
        send_slack_message(exception)

tracker.add_custom_handler(critical_error_alert)
```

### 5. Monitor Error Metrics

```python
# Periodic health check
metrics = tracker.get_metrics()
if metrics["total_errors"] > 1000:
    alert_operations_team("High error rate detected")
```

## Testing

### Unit Tests

```python
import pytest
from src.utils.error_tracking import (
    ErrorTracker,
    ErrorCategory,
    ErrorSeverity
)

def test_error_tracking():
    tracker = ErrorTracker()

    try:
        raise ValueError("Test error")
    except ValueError as exc:
        tracker.capture_exception(
            exc,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING
        )

    metrics = tracker.get_metrics()
    assert metrics["total_errors"] == 1
    assert metrics["by_category"]["validation"] == 1
```

### Integration Tests

```python
from fastapi.testclient import TestClient

def test_error_middleware():
    client = TestClient(app)

    # Trigger an error
    response = client.get("/api/nonexistent")

    # Check error was tracked
    tracker = get_error_tracker()
    metrics = tracker.get_metrics()
    assert metrics["total_errors"] > 0
```

## Monitoring Dashboard

### Access Error Metrics

```python
from fastapi import APIRouter
from src.utils.error_tracking import get_error_tracker

router = APIRouter()

@router.get("/admin/errors/metrics")
async def get_error_metrics():
    """Get current error metrics."""
    tracker = get_error_tracker()
    return tracker.get_metrics()
```

### Example Response

```json
{
    "total_errors": 245,
    "by_category": {
        "network": 150,
        "validation": 45,
        "file_io": 50
    },
    "by_severity": {
        "error": 200,
        "warning": 40,
        "critical": 5
    },
    "unique_error_types": 12
}
```

## Troubleshooting

### Error Tracking Not Initialized

```python
RuntimeError: Error tracking not initialized. Call initialize_error_tracking() first.
```

**Solution**: Initialize error tracking before use:
```python
from src.utils.error_tracking import initialize_error_tracking
initialize_error_tracking()
```

### Sentry Not Sending Events

**Possible causes**:
1. Invalid DSN
2. Sentry SDK not installed: `pip install sentry-sdk[fastapi]`
3. Firewall blocking outbound connections
4. Sample rate set too low

**Debug**:
```python
import sentry_sdk
sentry_sdk.init(
    dsn="your-dsn",
    debug=True  # Enable debug logging
)
```

### High Memory Usage

If error metrics are consuming too much memory:

```python
# Periodically reset metrics
tracker = get_error_tracker()
metrics = tracker.get_metrics()
# Save metrics to database/file
save_metrics_to_storage(metrics)
# Reset
tracker.reset_metrics()
```

## Security Considerations

1. **Don't log sensitive data**:
   ```python
   # BAD
   tracker.capture_exception(exc, context={"password": user.password})

   # GOOD
   tracker.capture_exception(exc, context={"user_id": user.id})
   ```

2. **Sanitize error messages**:
   ```python
   # Don't expose internal paths or credentials in production
   ```

3. **Set `send_default_pii=False`** in Sentry:
   ```python
   sentry_sdk.init(dsn="...", send_default_pii=False)
   ```

4. **Restrict access to error metrics**:
   ```python
   @router.get("/admin/errors/metrics")
   async def get_error_metrics(current_user: User = Depends(require_admin)):
       ...
   ```

## Further Reading

- [Sentry Python Documentation](https://docs.sentry.io/platforms/python/)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
