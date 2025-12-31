# Monitoring Configuration

Comprehensive monitoring setup for Website Status Checker using Prometheus and Grafana.

## Overview

The monitoring stack includes:
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Metrics visualization and dashboards
- **Alert Rules**: Pre-configured alerts for common issues

## Quick Start

### Enable Monitoring Stack

```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d

# Check services
docker-compose ps
```

**Services:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/password from .env)
- Application Metrics: http://localhost:8000/metrics

## Directory Structure

```
monitoring/
├── prometheus.yml              # Prometheus configuration
├── alerts/
│   └── website-checker-alerts.yml  # Alert rules
├── grafana-dashboards/
│   ├── dashboard-provisioning.yml  # Dashboard config
│   └── website-checker-dashboard.json  # Main dashboard
└── grafana-datasources/
    └── datasource.yml          # Prometheus datasource
```

## Prometheus Configuration

### Metrics Collection

Prometheus scrapes metrics from the application every 10 seconds:

```yaml
scrape_configs:
  - job_name: 'website-checker'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Available Metrics

#### HTTP Metrics
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Currently processing requests

#### Job Metrics
- `active_jobs` - Number of currently active jobs
- `job_results_total` - Total job results processed
- `job_processing_duration_seconds` - Job processing time

#### Database Metrics
- `database_connections` - Connection pool status (in_use, idle)
- `database_query_duration_seconds` - Query execution time

#### System Metrics
- `memory_usage_bytes` - Application memory usage
- `cpu_percent` - CPU utilization percentage
- `disk_usage_percent` - Disk space usage

### Alert Rules

#### Critical Alerts

**ApplicationDown**
- Triggers when application is unreachable for 2+ minutes
- Action: Check application logs, restart if needed

**VeryHighRequestLatency**
- Triggers when P95 latency >5s for 2+ minutes
- Action: Check system resources, investigate slow queries

**DatabaseDown**
- Triggers when database connection lost for 1+ minute
- Action: Check database service, verify credentials

**CriticalDiskSpace**
- Triggers when disk usage >90%
- Action: Clean up old files, expand storage

#### Warning Alerts

**HighErrorRate**
- Triggers when error rate >5% for 5+ minutes
- Action: Check application logs for errors

**HighMemoryUsage**
- Triggers when memory >3GB for 5+ minutes
- Action: Check for memory leaks, consider scaling

**HighCPUUsage**
- Triggers when CPU >80% for 5+ minutes
- Action: Check for inefficient operations, consider scaling

**TooManyActiveJobs**
- Triggers when >8 concurrent jobs for 10+ minutes
- Action: Review job processing capacity

#### Info Alerts

**RateLimitingTriggered**
- Triggers when rate limits frequently exceeded
- Action: Review API usage patterns

### Configuring Alertmanager

To receive alert notifications, set up Alertmanager:

1. Create `alertmanager.yml`:
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@yourdomain.com'
        from: 'monitoring@yourdomain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

2. Update `docker-compose.yml`:
```yaml
services:
  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"
```

3. Update `prometheus.yml`:
```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

## Grafana Configuration

### Access Grafana

1. Open http://localhost:3000
2. Login with credentials from `.env`:
   - Username: `admin` (default)
   - Password: Set in `GRAFANA_PASSWORD`

### Pre-configured Dashboard

The **Website Status Checker - Overview** dashboard includes:

**Request Metrics Panel**
- Request rate by endpoint
- Success vs error rates

**Performance Panel**
- Request latency (P50, P95, P99)
- Active jobs gauge

**Database Panel**
- Connection pool status
- Query performance

**System Resources Panel**
- Memory usage over time
- CPU utilization

**HTTP Status Codes Panel**
- Status code distribution
- Error patterns

### Creating Custom Dashboards

1. Click **+** → **Dashboard**
2. Add panels with PromQL queries
3. Example queries:

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate percentage
(rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Memory growth rate
deriv(memory_usage_bytes[15m])
```

## Common PromQL Queries

### Application Health

```promql
# Is the application up?
up{job="website-checker"}

# Request rate (requests per second)
rate(http_requests_total[5m])

# Success rate
rate(http_requests_total{status="200"}[5m]) / rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])
```

### Performance

```promql
# Average latency
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Resources

```promql
# Memory usage in GB
memory_usage_bytes / 1024 / 1024 / 1024

# CPU percentage
cpu_percent

# Disk usage percentage
disk_usage_percent
```

### Jobs

```promql
# Active jobs
active_jobs

# Job completion rate
rate(job_results_total[5m])

# Job processing duration
job_processing_duration_seconds
```

## Monitoring Best Practices

### 1. Set Appropriate Alert Thresholds

Adjust alert thresholds based on your SLAs:
- Edit `monitoring/alerts/website-checker-alerts.yml`
- Restart Prometheus: `docker-compose restart prometheus`

### 2. Monitor Alert Fatigue

- Review triggered alerts weekly
- Adjust thresholds for noisy alerts
- Remove alerts that don't require action

### 3. Regular Metric Reviews

- Check dashboards daily for anomalies
- Review trends weekly
- Capacity planning monthly

### 4. Data Retention

Prometheus default retention: 15 days

To change retention:
```yaml
# docker-compose.yml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'  # Keep 30 days
```

### 5. Backup Prometheus Data

```bash
# Backup Prometheus data
docker run --rm -v website-status-checker_prometheus_data:/data -v $(pwd)/backups:/backup ubuntu tar czf /backup/prometheus_data.tar.gz /data

# Restore
docker run --rm -v website-status-checker_prometheus_data:/data -v $(pwd)/backups:/backup ubuntu tar xzf /backup/prometheus_data.tar.gz -C /
```

## Troubleshooting

### Prometheus Can't Scrape Metrics

**Check target status:**
http://localhost:9090/targets

**Common issues:**
1. Application not exposing metrics
   - Verify: `curl http://localhost:8000/metrics`
2. Network connectivity
   - Check: `docker-compose exec prometheus ping web`
3. Incorrect target configuration
   - Review `prometheus.yml`

### Grafana Dashboard Not Loading

**Check datasource connection:**
1. Grafana → Configuration → Data Sources
2. Click "Prometheus"
3. Click "Test" button

**If failed:**
- Verify Prometheus is running: `docker-compose ps prometheus`
- Check URL: Should be `http://prometheus:9090`

### Alerts Not Firing

**Check alert rules:**
http://localhost:9090/rules

**Verify:**
1. Rules are loaded correctly
2. Query returns data in Prometheus UI
3. Alertmanager is configured (if using)

### High Prometheus Memory Usage

**Reduce cardinality:**
- Limit label combinations
- Increase scrape interval
- Reduce retention period

**Monitor Prometheus:**
```promql
# Check metric cardinality
count(up) by (job)

# Memory usage
process_resident_memory_bytes{job="prometheus"}
```

## Integration with External Services

### Datadog

Export metrics to Datadog:
```yaml
# Add to docker-compose.yml
services:
  prometheus-datadog:
    image: datadog/agent:latest
    environment:
      - DD_API_KEY=your-api-key
      - DD_PROMETHEUS_SCRAPE_ENABLED=true
```

### Cloud Monitoring

- **AWS CloudWatch**: Use Prometheus remote write
- **Google Cloud Monitoring**: Use GCP exporter
- **Azure Monitor**: Use Azure exporter

## Performance Impact

Monitoring overhead:
- **CPU**: <2% additional usage
- **Memory**: ~100-200MB for Prometheus
- **Disk**: ~10MB per day (default retention)
- **Network**: ~1KB/s metrics traffic

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Alerting Best Practices](https://prometheus.io/docs/practices/alerting/)

---

**Need Help?**
- Check application logs: `docker-compose logs -f web`
- Check Prometheus logs: `docker-compose logs -f prometheus`
- Check Grafana logs: `docker-compose logs -f grafana`
