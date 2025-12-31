# Logging Configuration and Best Practices

This document describes the logging system implemented in the Website Status Checker, including configuration options, structured logging, and best practices.

## Overview

The logging system provides:
- **Structured logging** with JSON format support
- **Correlation IDs** for request tracking
- **Log rotation** to manage file sizes
- **Performance logging** for timing operations
- **Context-aware logging** with metadata
- **Module-level log filtering**

## Architecture

### Components

1. **Structured Logging** (`src/utils/logging_config.py`)
   - JSONFormatter for machine-readable logs
   - CorrelationFilter for request tracking
   - Log rotation with configurable limits
   - Context managers for temporary log context

2. **Request Logging Middleware** (`gui/middleware/logging.py`)
   - HTTP request/response logging
   - Performance tracking for slow requests
   - Correlation ID propagation

3. **Application Loggers**
   - CLI: Configured via command-line flags
   - GUI: Configured via environment variables
   - Core modules: Use correlation IDs for tracing

## Configuration

### Environment Variables

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log format: text or json
LOG_FORMAT=text

# Log file path (empty for stdout only)
LOG_FILE=logs/application.log
```

### CLI Arguments

```bash
# Verbose logging (INFO level)
python -m src.cli.main --verbose

# Debug logging (DEBUG level)
python -m src.cli.main --debug

# JSON-formatted logs
python -m src.cli.main --json-logs

# Save logs to file
python -m src.cli.main --log-file app.log

# Combined example
python -m src.cli.main --debug --json-logs --log-file debug.log
```

### Programmatic Configuration

```python
from src.utils.logging_config import setup_logging

# Text logging for development
setup_logging(
    log_level="INFO",
    log_format="text",
    log_file=None,
    enable_console=True
)

# JSON logging for production
setup_logging(
    log_level="WARNING",
    log_format="json",
    log_file="logs/production.log",
    max_bytes=100 * 1024 * 1024,  # 100MB
    backup_count=10  # Keep 10 old log files
)
```

## Log Formats

### Text Format (Development)

```
2025-01-15 10:23:45 - src.core.checker - INFO - [checker.py:156] - Processing URL: https://example.com
2025-01-15 10:23:46 - src.core.batch - WARNING - [batch.py:234] - Slow batch processing: 1523ms
2025-01-15 10:23:47 - api.requests - INFO - POST /api/upload/file - 200 in 234.56ms
```

### JSON Format (Production)

```json
{
  "timestamp": "2025-01-15T10:23:45.123Z",
  "level": "INFO",
  "logger": "src.core.checker",
  "message": "Processing URL: https://example.com",
  "module": "checker",
  "function": "check_url",
  "line": 156,
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

```json
{
  "timestamp": "2025-01-15T10:23:47.456Z",
  "level": "INFO",
  "logger": "api.requests",
  "message": "POST /api/upload/file - 200 in 234.56ms",
  "module": "logging",
  "function": "dispatch",
  "line": 98,
  "correlation_id": "b2c3d4e5-f6g7-8901-bcde-f12345678901",
  "event_type": "http_response",
  "method": "POST",
  "path": "/api/upload/file",
  "status_code": 200,
  "duration_ms": 234.56,
  "client_ip": "192.168.1.100"
}
```

## Usage Examples

### Basic Logging

```python
from src.utils.logging_config import get_logger

# Get logger for current module
logger = get_logger(__name__)

# Simple log messages
logger.debug("Debug information")
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error!")
```

### Logging with Context

```python
from src.utils.logging_config import get_logger

# Logger with correlation ID
logger = get_logger(__name__, correlation_id="request-123")

logger.info("Processing request", extra={
    "user_id": "user-456",
    "operation": "file_upload",
    "file_size": 1024000
})
```

### Logging with Temporary Context

```python
from src.utils.logging_config import get_logger, LogContext

logger = get_logger(__name__)

# Add context for a specific code block
with LogContext(logger, user_id="user-123", session_id="session-456"):
    logger.info("User action")  # Includes user_id and session_id
    logger.info("Another action")  # Also includes the context
# Context is removed after the block
```

### Performance Logging

```python
from src.utils.logging_config import get_logger, log_performance
import time

logger = get_logger(__name__)

start_time = time.time()
# ... perform operation ...
duration_ms = (time.time() - start_time) * 1000

log_performance(
    logger,
    "database_query",
    duration_ms,
    extra={
        "query_type": "SELECT",
        "table": "users",
        "rows_returned": 150
    }
)
```

### Exception Logging

```python
from src.utils.logging_config import log_exception

try:
    risky_operation()
except Exception as exc:
    log_exception(
        logger,
        exc,
        message="Failed to process data",
        extra={
            "input_file": "data.csv",
            "row_count": 1000
        }
    )
```

## Module-Level Log Filtering

### Configure Log Levels Per Module

```python
import logging

# Set different log levels for different modules
logging.getLogger('src.core.checker').setLevel(logging.DEBUG)
logging.getLogger('src.core.batch').setLevel(logging.INFO)
logging.getLogger('api.requests').setLevel(logging.WARNING)

# Reduce noise from third-party libraries
logging.getLogger('aiohttp').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.WARNING)
```

### Environment-Based Configuration

```python
from src.utils.logging_config import setup_logging
import os

# Development: verbose logging
if os.getenv('ENV') == 'development':
    setup_logging(log_level="DEBUG", log_format="text")

# Production: structured logging
elif os.getenv('ENV') == 'production':
    setup_logging(
        log_level="WARNING",
        log_format="json",
        log_file="logs/production.log"
    )
```

## Request/Response Logging (FastAPI)

### Automatic Request Logging

The FastAPI application automatically logs all HTTP requests and responses:

```json
{
  "timestamp": "2025-01-15T10:23:45Z",
  "level": "INFO",
  "event_type": "http_request",
  "method": "POST",
  "path": "/api/upload/file",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "correlation_id": "abc-123"
}
```

```json
{
  "timestamp": "2025-01-15T10:23:46Z",
  "level": "INFO",
  "event_type": "http_response",
  "method": "POST",
  "path": "/api/upload/file",
  "status_code": 200,
  "duration_ms": 456.78,
  "correlation_id": "abc-123"
}
```

### Correlation ID Tracking

Every HTTP request is assigned a unique correlation ID that:
- Appears in all logs for that request
- Is returned in response header `X-Correlation-ID`
- Can be used to trace request flow across services

```bash
# Make request
curl -v https://api.example.com/upload

# Response includes correlation ID
< X-Correlation-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
< X-Response-Time: 123.45ms
```

### Performance Logging

Slow requests are automatically logged as warnings:

```json
{
  "timestamp": "2025-01-15T10:23:50Z",
  "level": "WARNING",
  "event_type": "slow_request",
  "method": "POST",
  "path": "/api/process/batch",
  "duration_ms": 3456.78,
  "threshold_ms": 1000
}
```

## Log Aggregation

### ELK Stack (Elasticsearch, Logstash, Kibana)

#### Logstash Configuration

```ruby
input {
  file {
    path => "/var/log/website-checker/*.log"
    codec => json
  }
}

filter {
  # Parse timestamp
  date {
    match => [ "timestamp", "ISO8601" ]
    target => "@timestamp"
  }

  # Add tags based on log level
  if [level] == "ERROR" or [level] == "CRITICAL" {
    mutate {
      add_tag => [ "error" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "website-checker-%{+YYYY.MM.dd}"
  }
}
```

#### Kibana Queries

```
# All errors in the last hour
level:ERROR AND @timestamp:[now-1h TO now]

# Slow requests
event_type:slow_request AND duration_ms:>1000

# Requests for specific correlation ID
correlation_id:"a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Error rate by endpoint
event_type:http_response AND status_code:>=500
```

### Grafana Loki

#### Promtail Configuration

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: website-checker
    static_configs:
      - targets:
          - localhost
        labels:
          job: website-checker
          __path__: /var/log/website-checker/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            logger: logger
            correlation_id: correlation_id
      - labels:
          level:
          logger:
```

#### LogQL Queries

```
# All logs for the application
{job="website-checker"}

# Error logs only
{job="website-checker"} | json | level="ERROR"

# Logs with specific correlation ID
{job="website-checker"} | json | correlation_id="abc-123"

# HTTP errors
{job="website-checker"} | json | event_type="http_response" | status_code>=500

# Rate of errors per minute
rate({job="website-checker"} | json | level="ERROR"[1m])
```

## Best Practices

### 1. Use Appropriate Log Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug(f"URL normalized: {original_url} -> {normalized_url}")

# INFO: General informational messages
logger.info(f"Processing batch {batch_num}/{total_batches}")

# WARNING: Potentially harmful situations
logger.warning(f"Slow request detected: {duration_ms}ms")

# ERROR: Error events that don't stop execution
logger.error(f"Failed to process URL {url}: {error}")

# CRITICAL: Severe errors causing application failure
logger.critical("Database connection lost, shutting down")
```

### 2. Add Contextual Information

```python
# BAD: Not enough context
logger.error("Processing failed")

# GOOD: Include relevant details
logger.error(
    "Batch processing failed",
    extra={
        "batch_number": batch_num,
        "input_file": input_file,
        "urls_processed": urls_processed,
        "error_type": type(exc).__name__
    }
)
```

### 3. Use Correlation IDs

```python
# In batch processing
correlation_id = str(uuid.uuid4())
logger = get_logger(__name__, correlation_id=correlation_id)

# All subsequent logs will include the correlation ID
logger.info("Starting batch processing")
logger.info("Processed 100 URLs")
logger.info("Batch complete")
```

### 4. Don't Log Sensitive Data

```python
# BAD: Logging sensitive information
logger.info(f"User password: {password}")
logger.info(f"API key: {api_key}")

# GOOD: Log only non-sensitive identifiers
logger.info(f"User authenticated", extra={"user_id": user.id})
logger.info(f"API request successful", extra={"endpoint": "/api/data"})
```

### 5. Use Structured Logging in Production

```python
# Development: Human-readable
setup_logging(log_level="DEBUG", log_format="text")

# Production: Machine-parseable
setup_logging(
    log_level="INFO",
    log_format="json",
    log_file="logs/production.log"
)
```

### 6. Implement Log Rotation

```python
setup_logging(
    log_level="INFO",
    log_format="json",
    log_file="logs/application.log",
    max_bytes=100 * 1024 * 1024,  # 100MB per file
    backup_count=10  # Keep 10 rotated files
)
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Error Rate**: Percentage of ERROR/CRITICAL logs
2. **Request Duration**: p50, p95, p99 response times
3. **Slow Requests**: Requests exceeding threshold
4. **Error Categories**: Group errors by type
5. **Correlation ID Usage**: Track request flows

### Alert Examples

```yaml
# Prometheus AlertManager rules
groups:
  - name: website-checker
    rules:
      - alert: HighErrorRate
        expr: |
          rate(log_messages_total{level="ERROR"}[5m]) > 10
        annotations:
          summary: "High error rate detected"

      - alert: SlowRequests
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_ms_bucket[5m])
          ) > 5000
        annotations:
          summary: "95th percentile request time > 5s"
```

## Troubleshooting

### Issue: Logs Not Appearing

**Check:**
1. Log level is appropriate (`DEBUG` shows everything)
2. Logger is properly initialized
3. Console/file handlers are configured

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Test message")
```

### Issue: Log File Not Created

**Check:**
1. Directory exists and is writable
2. File path is absolute or relative to correct directory
3. Permissions allow file creation

```python
from pathlib import Path

log_file = Path("logs/application.log")
log_file.parent.mkdir(parents=True, exist_ok=True)
```

### Issue: Correlation IDs Not Appearing

**Check:**
1. CorrelationFilter is added to logger
2. Using `get_logger()` with correlation_id parameter
3. Middleware is properly configured (for HTTP requests)

```python
logger = get_logger(__name__, correlation_id="test-123")
logger.info("Test")  # Should include correlation_id
```

### Issue: JSON Logs Malformed

**Check:**
1. All extra fields are JSON-serializable
2. Custom objects are converted to strings
3. JSONFormatter is being used

```python
# Custom object serialization
logger.info(
    "Processing",
    extra={
        "timestamp": datetime.now().isoformat(),
        "result": str(result),  # Convert to string
    }
)
```

## Further Reading

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/)
- [ELK Stack Guide](https://www.elastic.co/guide/index.html)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
