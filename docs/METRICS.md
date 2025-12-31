# Prometheus Metrics and Monitoring

This document describes the Prometheus metrics implementation for the Website Status Checker, including available metrics, Grafana dashboards, and monitoring best practices.

## Overview

The metrics system provides comprehensive observability through:
- **HTTP request metrics** (count, duration, size)
- **Business metrics** (URLs checked, batch processing)
- **System metrics** (CPU, memory, disk)
- **Error tracking metrics**
- **Prometheus-compatible endpoint** for scraping
- **Grafana dashboard templates**

## Available Metrics

### HTTP Request Metrics

#### `http_requests_total`
**Type:** Counter
**Description:** Total number of HTTP requests
**Labels:**
- `method`: HTTP method (GET, POST, PUT, DELETE)
- `endpoint`: Normalized endpoint path
- `status_code`: HTTP status code (200, 404, 500, etc.)

**Example:**
```
http_requests_total{method="POST",endpoint="/api/upload/file",status_code="200"} 1523
http_requests_total{method="GET",endpoint="/api/results/{id}",status_code="200"} 842
```

#### `http_request_duration_seconds`
**Type:** Histogram
**Description:** HTTP request duration in seconds
**Labels:**
- `method`: HTTP method
- `endpoint`: Normalized endpoint path

**Buckets:** 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0

**Example:**
```
http_request_duration_seconds_bucket{method="POST",endpoint="/api/process/batch",le="0.5"} 45
http_request_duration_seconds_bucket{method="POST",endpoint="/api/process/batch",le="1.0"} 120
http_request_duration_seconds_sum{method="POST",endpoint="/api/process/batch"} 234.5
http_request_duration_seconds_count{method="POST",endpoint="/api/process/batch"} 150
```

####http_request_size_bytes`
**Type:** Histogram
**Description:** HTTP request size in bytes
**Labels:**
- `method`: HTTP method
- `endpoint`: Normalized endpoint path

#### `http_response_size_bytes`
**Type:** Histogram
**Description:** HTTP response size in bytes
**Labels:**
- `method`: HTTP method
- `endpoint`: Normalized endpoint path

#### `http_requests_in_progress`
**Type:** Gauge
**Description:** Number of HTTP requests currently being processed
**Labels:**
- `method`: HTTP method
- `endpoint`: Normalized endpoint path

### Business Metrics

#### `urls_checked_total`
**Type:** Counter
**Description:** Total number of URLs checked
**Labels:**
- `status_result`: Check result (ACTIVE, INACTIVE, ERROR, TIMEOUT)

**Example:**
```
urls_checked_total{status_result="ACTIVE"} 45230
urls_checked_total{status_result="INACTIVE"} 3421
urls_checked_total{status_result="ERROR"} 892
```

#### `urls_check_duration_seconds`
**Type:** Histogram
**Description:** URL check duration in seconds
**Buckets:** 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0

#### `batch_processing_total`
**Type:** Counter
**Description:** Total number of batch processing jobs
**Labels:**
- `status`: Processing status (success, failure, cancelled)

#### `batch_processing_duration_seconds`
**Type:** Histogram
**Description:** Batch processing duration in seconds

#### `active_jobs`
**Type:** Gauge
**Description:** Number of currently active processing jobs

### File Upload Metrics

#### `file_uploads_total`
**Type:** Counter
**Description:** Total file uploads
**Labels:**
- `status`: Upload status (success, failure)
- `file_type`: File extension (csv, xlsx, txt)

#### `file_upload_size_bytes`
**Type:** Histogram
**Description:** File upload size in bytes
**Buckets:** 1KB, 10KB, 100KB, 1MB, 10MB, 100MB

### Error Metrics

#### `errors_total`
**Type:** Counter
**Description:** Total number of errors
**Labels:**
- `error_type`: Error class name
- `error_category`: Error category (network, validation, etc.)

### System Metrics

#### `system_cpu_usage_percent`
**Type:** Gauge
**Description:** System CPU usage percentage

#### `system_memory_usage_bytes`
**Type:** Gauge
**Description:** System memory usage in bytes

#### `system_memory_available_bytes`
**Type:** Gauge
**Description:** System available memory in bytes

#### `process_memory_usage_bytes`
**Type:** Gauge
**Description:** Process memory usage in bytes

### Application Info

#### `app_info`
**Type:** Info
**Description:** Application metadata
**Labels:**
- `name`: Application name
- `version`: Application version
- `environment`: Environment (development, staging, production)

## Configuration

### Environment Variables

```bash
# Enable Prometheus metrics
ENABLE_METRICS=true

# Metrics endpoint path (default: /metrics)
METRICS_PATH=/metrics
```

### Access Metrics Endpoint

```bash
# Get Prometheus metrics
curl http://localhost:8000/metrics

# Get human-readable summary
curl http://localhost:8000/metrics/summary
```

### Example Output

**Prometheus Format (`/metrics`):**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/results",status_code="200"} 1234.0
http_requests_total{method="POST",endpoint="/api/upload/file",status_code="200"} 567.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="POST",endpoint="/api/process/batch",le="0.5"} 45.0
http_request_duration_seconds_bucket{method="POST",endpoint="/api/process/batch",le="1.0"} 120.0
http_request_duration_seconds_sum{method="POST",endpoint="/api/process/batch"} 234.5
http_request_duration_seconds_count{method="POST",endpoint="/api/process/batch"} 150.0

# HELP urls_checked_total Total number of URLs checked
# TYPE urls_checked_total counter
urls_checked_total{status_result="ACTIVE"} 45230.0
urls_checked_total{status_result="INACTIVE"} 3421.0
```

**JSON Summary (`/metrics/summary`):**
```json
{
  "http": {
    "total_requests": 1801
  },
  "urls": {
    "total_checked": 48651
  },
  "batch": {
    "total_jobs": 156,
    "active_jobs": 3
  },
  "uploads": {
    "total_uploads": 567
  },
  "errors": {
    "total_errors": 892
  }
}
```

## Prometheus Setup

### 1. Install Prometheus

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*
```

### 2. Configure Prometheus

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'website-checker'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### 3. Run Prometheus

```bash
./prometheus --config.file=prometheus.yml
```

Access Prometheus UI at `http://localhost:9090`

### 4. Query Examples

```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# Average request duration
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Error rate
sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# Active vs Inactive URLs ratio
urls_checked_total{status_result="ACTIVE"} / urls_checked_total{status_result="INACTIVE"}

# CPU usage
system_cpu_usage_percent

# Memory usage percentage
(system_memory_usage_bytes / (system_memory_usage_bytes + system_memory_available_bytes)) * 100
```

## Grafana Dashboard

### Setup

1. **Install Grafana:**
```bash
wget https://dl.grafana.com/oss/release/grafana-10.0.0.linux-amd64.tar.gz
tar -zxvf grafana-*.tar.gz
cd grafana-*
./bin/grafana-server
```

2. **Access Grafana:** `http://localhost:3000` (admin/admin)

3. **Add Prometheus Data Source:**
   - Configuration → Data Sources → Add data source
   - Select Prometheus
   - URL: `http://localhost:9090`
   - Save & Test

### Dashboard JSON

Create a new dashboard and import this JSON:

```json
{
  "dashboard": {
    "title": "Website Status Checker Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (method)"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Request Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))"
          }
        ],
        "type": "graph"
      },
      {
        "title": "URLs Checked by Status",
        "targets": [
          {
            "expr": "urls_checked_total"
          }
        ],
        "type": "piechart"
      },
      {
        "title": "Active Jobs",
        "targets": [
          {
            "expr": "active_jobs"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(errors_total[5m])) by (error_category)"
          }
        ],
        "type": "graph"
      },
      {
        "title": "System CPU Usage",
        "targets": [
          {
            "expr": "system_cpu_usage_percent"
          }
        ],
        "type": "gauge"
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "(system_memory_usage_bytes / (system_memory_usage_bytes + system_memory_available_bytes)) * 100"
          }
        ],
        "type": "gauge"
      }
    ]
  }
}
```

### Key Dashboard Panels

1. **Request Rate** - Requests per second by method
2. **Request Duration** - p50, p95, p99 latencies
3. **Error Rate** - Percentage of 5xx responses
4. **URLs Checked** - Breakdown by status (Active/Inactive/Error)
5. **Batch Processing** - Jobs completed, duration distribution
6. **System Resources** - CPU, memory, disk usage
7. **Active Jobs** - Current processing jobs
8. **File Uploads** - Upload rate and sizes

## Alerting

### Prometheus Alert Rules

Create `alerts.yml`:

```yaml
groups:
  - name: website_checker_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status_code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m]))
          > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighRequestLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          ) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High request latency on {{ $labels.endpoint }}"
          description: "95th percentile latency is {{ $value }}s"

      - alert: HighMemoryUsage
        expr: |
          (system_memory_usage_bytes / (system_memory_usage_bytes + system_memory_available_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"

      - alert: TooManyActiveJobs
        expr: active_jobs > 50
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Too many active jobs"
          description: "{{ $value }} jobs are currently active"

      - alert: HighURLErrorRate
        expr: |
          rate(urls_checked_total{status_result="ERROR"}[10m])
          /
          rate(urls_checked_total[10m])
          > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High URL check error rate"
          description: "{{ $value | humanizePercentage }} of URL checks are failing"
```

### Alert Manager Configuration

`alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'Website Checker Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}\n{{ end }}'
```

## Usage Examples

### Track Business Metrics

```python
from gui.middleware.metrics import (
    track_url_check,
    track_batch_processing,
    track_file_upload,
    track_error
)

# Track URL check
track_url_check(status_result="ACTIVE", duration_seconds=0.5)

# Track batch processing
track_batch_processing(status="success", duration_seconds=120.5)

# Track file upload
track_file_upload(status="success", file_type="csv", size_bytes=1024000)

# Track error
track_error(error_type="ConnectionError", error_category="network")
```

### Monitor Performance

```bash
# Check current metrics
curl http://localhost:8000/metrics/summary | jq

# Query specific metric
curl http://localhost:8000/metrics | grep urls_checked_total

# Monitor error rate
watch -n 1 'curl -s http://localhost:8000/metrics | grep errors_total'
```

## Best Practices

1. **Use Labels Wisely**
   - Keep label cardinality low (avoid user IDs, UUIDs)
   - Use normalized endpoints (`/api/results/{id}` not `/api/results/12345`)

2. **Choose Appropriate Metric Types**
   - Counter: Cumulative values (requests, errors)
   - Gauge: Current values (active jobs, memory)
   - Histogram: Distributions (duration, size)

3. **Set Meaningful Buckets**
   - Duration: 0.01s to 10s for API requests
   - Size: 1KB to 100MB for file uploads

4. **Monitor What Matters**
   - **The Four Golden Signals:**
     - Latency (request duration)
     - Traffic (request rate)
     - Errors (error rate)
     - Saturation (resource usage)

5. **Alert on Symptoms, Not Causes**
   - Alert on high error rate, not specific errors
   - Alert on slow responses, not high CPU

## Troubleshooting

### Metrics Not Appearing

**Check:**
1. Metrics enabled: `ENABLE_METRICS=true`
2. Endpoint accessible: `curl http://localhost:8000/metrics`
3. Prometheus scraping: Check targets in Prometheus UI

### High Cardinality Issues

**Problem:** Too many unique label combinations
**Solution:**
- Normalize endpoints (use `{id}` placeholders)
- Avoid user-specific labels
- Review metric design

### Missing Metrics

**Check:**
1. Middleware is properly configured
2. Code paths are being executed
3. Metrics are exported (check `/metrics` endpoint)

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [The Four Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/)
