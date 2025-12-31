# Production Runbook

Operational procedures and incident response guide for Website Status Checker.

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Normal Operations](#normal-operations)
3. [Incident Response](#incident-response)
4. [Common Issues](#common-issues)
5. [Escalation Procedures](#escalation-procedures)
6. [Maintenance Windows](#maintenance-windows)

---

## System Overview

### Architecture

```
┌─────────────┐
│   Users     │
└──────┬──────┘
       │
┌──────▼──────────────┐
│   Load Balancer/    │
│   Nginx/Ingress     │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│  Website Checker    │◄─── Prometheus (metrics)
│  (3+ instances)     │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│   PostgreSQL DB     │
│  (with backups)     │
└─────────────────────┘
```

### Service Dependencies

- **PostgreSQL**: Required for operation
- **Persistent Storage**: Required for uploads/exports
- **Network**: Outbound HTTP/HTTPS for checking websites

### SLA Targets

- **Availability**: 99% uptime
- **Latency**: P95 <1s, P99 <2s
- **Error Rate**: <1%
- **Recovery Time Objective (RTO)**: 15 minutes
- **Recovery Point Objective (RPO)**: 24 hours

---

## Normal Operations

### Daily Checks

**Every Morning (09:00)**

```bash
# 1. Check service health
curl https://checker.yourdomain.com/health/detailed

# 2. Review overnight alerts
curl http://prometheus:9090/api/v1/alerts | jq '.data.alerts'

# 3. Check resource usage
docker stats --no-stream

# 4. Verify last backup
ls -lh backups/ | tail -1

# 5. Review error logs
docker-compose logs --since 24h web | grep -i error | wc -l
```

**Expected Results:**
- Health status: "healthy"
- Active alerts: 0
- Memory usage: <2GB per instance
- CPU usage: <50%
- Backup from last night exists
- Error count: <10

### Weekly Tasks

**Every Monday (10:00)**

1. **Review Metrics Trends**
   ```bash
   # Open Grafana dashboard
   # Check weekly trends for:
   # - Request rate
   # - Error rate
   # - Latency
   # - Resource usage
   ```

2. **Review Alert Noise**
   ```bash
   # Check Prometheus alerts history
   # Adjust thresholds for noisy alerts
   # Document any changes
   ```

3. **Test Backups**
   ```bash
   # Restore latest backup to test environment
   ./scripts/restore.sh backups/latest_backup.sql.gz

   # Verify data integrity
   docker-compose exec db psql -U checker -d website_checker -c "SELECT COUNT(*) FROM jobs;"
   ```

4. **Review Disk Usage**
   ```bash
   # Check disk space
   df -h

   # Clean old files if needed
   ./scripts/cleanup.sh 168  # 7 days
   ```

5. **Update Dependencies** (if needed)
   ```bash
   # Check for security updates
   pip list --outdated

   # Review and apply critical updates
   ```

### Monthly Tasks

**First Day of Month**

1. **Capacity Planning Review**
   - Review 30-day usage trends
   - Project next 3 months growth
   - Plan scaling if needed

2. **Security Audit**
   - Review API key usage
   - Rotate admin keys
   - Check access logs for anomalies

3. **Disaster Recovery Test**
   - Full backup/restore drill
   - Document recovery time
   - Update procedures if needed

4. **Documentation Review**
   - Update runbook with new issues
   - Review and update alert descriptions
   - Update contact information

---

## Incident Response

### Severity Levels

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **P0 - Critical** | Complete outage | 5 minutes | Application down |
| **P1 - High** | Major degradation | 15 minutes | Database unreachable |
| **P2 - Medium** | Partial degradation | 1 hour | High error rate |
| **P3 - Low** | Minor issue | Next business day | Slow queries |

### P0 - Critical: Application Down

**Alert**: `ApplicationDown`

**Symptoms:**
- Health check failing for >2 minutes
- Users cannot access service
- All instances unreachable

**Response Procedure:**

1. **Verify the Issue** (1 minute)
   ```bash
   # Check if truly down
   curl https://checker.yourdomain.com/health

   # Check service status
   docker-compose ps
   # OR
   kubectl get pods -n website-checker
   ```

2. **Immediate Actions** (2-3 minutes)
   ```bash
   # Docker Compose
   docker-compose restart web

   # Kubernetes
   kubectl rollout restart deployment/website-checker -n website-checker
   ```

3. **Check Dependencies** (2 minutes)
   ```bash
   # Verify database
   docker-compose exec db pg_isready

   # Check disk space
   df -h

   # Check memory
   free -h
   ```

4. **Review Logs** (3 minutes)
   ```bash
   # Check for errors
   docker-compose logs --tail=100 web | grep -i error

   # Check for out of memory
   docker-compose logs web | grep -i "oom\|out of memory"
   ```

5. **Escalate if Not Resolved** (5 minutes)
   - Contact on-call engineer
   - Provide logs and symptoms
   - Prepare for deeper investigation

**Recovery Verification:**
```bash
# Confirm health
curl https://checker.yourdomain.com/health/detailed

# Check metrics
curl https://checker.yourdomain.com/metrics | grep up

# Test functionality
curl -X POST https://checker.yourdomain.com/api/jobs \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@test.csv"
```

**Post-Incident:**
- Document root cause
- Update runbook if needed
- Create JIRA ticket for prevention

### P1 - High: Database Unreachable

**Alert**: `DatabaseDown`

**Symptoms:**
- Application errors: "could not connect to database"
- Health check shows database: "unhealthy"
- Connection timeout errors

**Response Procedure:**

1. **Check Database Status** (1 minute)
   ```bash
   # Docker
   docker-compose ps db
   docker-compose exec db pg_isready

   # Kubernetes
   kubectl get pods -n website-checker -l app=postgres
   kubectl exec -n website-checker deployment/postgres -- pg_isready
   ```

2. **Restart Database** (2-3 minutes)
   ```bash
   # Docker Compose
   docker-compose restart db

   # Kubernetes
   kubectl rollout restart deployment/postgres -n website-checker
   ```

3. **Check Connection String** (1 minute)
   ```bash
   # Verify DATABASE_URL
   docker-compose exec web env | grep DATABASE_URL

   # Test connection
   docker-compose exec web python -c "from gui.database.session import engine; engine.connect()"
   ```

4. **Check Resources** (2 minutes)
   ```bash
   # Check database logs
   docker-compose logs --tail=100 db

   # Check disk space
   docker exec $(docker-compose ps -q db) df -h

   # Check memory
   docker stats --no-stream $(docker-compose ps -q db)
   ```

5. **Restore from Backup if Corrupted** (if needed)
   ```bash
   # Stop application
   docker-compose stop web

   # Restore database
   ./scripts/restore.sh backups/latest_backup.sql.gz

   # Restart everything
   docker-compose up -d
   ```

**Recovery Verification:**
```bash
# Check connection
docker-compose exec db psql -U checker -d website_checker -c "SELECT 1;"

# Verify data
docker-compose exec db psql -U checker -d website_checker -c "SELECT COUNT(*) FROM jobs;"

# Check application health
curl http://localhost:8000/health/detailed | jq '.database'
```

### P2 - Medium: High Error Rate

**Alert**: `HighErrorRate`

**Symptoms:**
- Error rate >5% for 5+ minutes
- 500 errors in logs
- Some requests failing

**Response Procedure:**

1. **Identify Error Pattern** (3 minutes)
   ```bash
   # Check recent errors
   docker-compose logs --since 10m web | grep "ERROR\|500"

   # Check error distribution
   curl http://localhost:8000/metrics | grep http_requests_total | grep "500\|502\|503"

   # Identify failing endpoints
   docker-compose logs web | grep "500" | awk '{print $7}' | sort | uniq -c | sort -rn
   ```

2. **Check System Resources** (2 minutes)
   ```bash
   # Memory pressure?
   docker stats --no-stream

   # Disk full?
   df -h

   # High CPU?
   docker stats --no-stream | grep web
   ```

3. **Check External Dependencies** (2 minutes)
   ```bash
   # Database responsive?
   docker-compose exec db pg_isready

   # Network issues?
   docker-compose exec web ping -c 3 8.8.8.8
   ```

4. **Mitigate** (3 minutes)
   ```bash
   # If resource issue, scale up
   docker-compose up -d --scale web=5
   # OR Kubernetes
   kubectl scale deployment website-checker -n website-checker --replicas=5

   # If memory leak, restart
   docker-compose restart web
   ```

5. **Monitor Recovery** (ongoing)
   ```bash
   # Watch error rate
   watch -n 5 'curl -s http://localhost:8000/metrics | grep http_requests_total | grep "500"'
   ```

**Root Cause Analysis:**
- Review application logs for stack traces
- Check for recent deployments/changes
- Correlate with traffic patterns
- Create bug ticket if needed

### P2 - Medium: High Latency

**Alert**: `HighRequestLatency`

**Symptoms:**
- P95 latency >2s for 5+ minutes
- Slow response times
- User complaints about performance

**Response Procedure:**

1. **Identify Slow Endpoints** (3 minutes)
   ```bash
   # Check latency by endpoint
   curl http://localhost:8000/metrics | grep duration_seconds

   # Check database query performance
   docker-compose exec db psql -U checker -d website_checker -c "
     SELECT query, calls, total_time, mean_time
     FROM pg_stat_statements
     ORDER BY mean_time DESC
     LIMIT 10;"
   ```

2. **Check for Resource Bottlenecks** (2 minutes)
   ```bash
   # CPU bound?
   docker stats --no-stream | grep web

   # I/O bound?
   docker stats --no-stream | grep -E "BLOCK|disk"

   # Database connections exhausted?
   curl http://localhost:8000/health/detailed | jq '.metrics.database_connections'
   ```

3. **Quick Fixes** (3 minutes)
   ```bash
   # Scale horizontally
   docker-compose up -d --scale web=5

   # Clear old jobs to reduce DB load
   ./scripts/cleanup.sh 6  # 6 hours

   # Restart to clear any memory issues
   docker-compose restart web
   ```

4. **Monitor Improvement** (ongoing)
   ```bash
   # Watch P95 latency
   watch -n 5 'curl -s http://localhost:8000/metrics | grep quantile'
   ```

**Long-term Solutions:**
- Add database indexes
- Optimize slow queries
- Implement caching
- Increase resources

### P3 - Low: Elevated Resource Usage

**Alert**: `HighMemoryUsage` or `HighCPUUsage`

**Response Procedure:**

1. **Verify the Alert**
   ```bash
   # Check actual usage
   docker stats --no-stream

   # Check trends in Grafana
   # Open dashboard and review last 24h
   ```

2. **Identify Cause**
   ```bash
   # Memory leak?
   # Check if memory steadily increasing

   # Too many active jobs?
   curl http://localhost:8000/health/detailed | jq '.metrics.active_jobs'

   # Old files not cleaned?
   du -sh gui/uploads gui/exports
   ```

3. **Take Action**
   ```bash
   # Run cleanup
   ./scripts/cleanup.sh

   # Restart if memory leak suspected
   docker-compose restart web

   # Scale if high load
   docker-compose up -d --scale web=4
   ```

4. **Create Ticket**
   - Document findings
   - Plan long-term fix
   - Schedule investigation

---

## Common Issues

### Issue: "File upload fails with 413 error"

**Cause**: File size exceeds limit

**Solution:**
```bash
# Check current limit
grep MAX_UPLOAD_SIZE_MB .env

# Increase if needed
# Edit .env:
MAX_UPLOAD_SIZE_MB=200

# Restart
docker-compose restart web

# For nginx, also update:
# client_max_body_size 200M;
```

### Issue: "API key authentication fails"

**Cause**: Invalid or expired key

**Solution:**
```bash
# Verify key exists
curl "http://localhost:8000/api/admin/api-keys?admin_key=ADMIN_KEY"

# Create new key
docker-compose exec web python scripts/create_api_key.py --name "New Key"

# Test new key
curl -H "X-API-Key: NEW_KEY" http://localhost:8000/api/admin/status
```

### Issue: "Jobs stuck in processing"

**Cause**: Worker crashed or hung

**Solution:**
```bash
# Check active jobs
curl http://localhost:8000/health/detailed | jq '.metrics.active_jobs'

# Restart workers
docker-compose restart web

# Check job status
docker-compose exec db psql -U checker -d website_checker -c "
  SELECT id, status, created_at, updated_at
  FROM jobs
  WHERE status = 'processing'
  ORDER BY updated_at DESC
  LIMIT 10;"

# Manually mark as failed if needed
docker-compose exec db psql -U checker -d website_checker -c "
  UPDATE jobs
  SET status = 'failed', error_message = 'Worker crashed'
  WHERE status = 'processing' AND updated_at < NOW() - INTERVAL '1 hour';"
```

### Issue: "Database migration failed"

**Cause**: Schema conflict or syntax error

**Solution:**
```bash
# Check current version
docker-compose exec web python -m alembic current

# Check migration history
docker-compose exec web python -m alembic history

# Rollback one version
docker-compose exec web python -m alembic downgrade -1

# Review migration file
# Fix issues in alembic/versions/

# Try again
docker-compose exec web python -m alembic upgrade head
```

### Issue: "Prometheus can't scrape metrics"

**Cause**: Network connectivity or metrics endpoint issue

**Solution:**
```bash
# Test metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets'

# Verify network connectivity
docker-compose exec prometheus ping web

# Restart Prometheus
docker-compose restart prometheus
```

---

## Escalation Procedures

### Level 1 - On-Call Engineer

**Contact:** Check PagerDuty/on-call schedule
**Response Time:** 5 minutes

**Responsibilities:**
- Initial incident response
- Follow runbook procedures
- Escalate to Level 2 if unresolved in 15 minutes

### Level 2 - Senior Engineer

**Contact:** Check escalation matrix
**Response Time:** 15 minutes

**Responsibilities:**
- Deep troubleshooting
- Database recovery
- Code fixes if needed
- Escalate to Level 3 for architectural issues

### Level 3 - Engineering Lead

**Contact:** Check contact list
**Response Time:** 30 minutes

**Responsibilities:**
- Architectural decisions
- Major incident coordination
- External vendor engagement

### External Contacts

| Service | Contact | Purpose |
|---------|---------|---------|
| Cloud Provider | support.aws.com | Infrastructure issues |
| Database Vendor | support.postgresql.org | PostgreSQL issues |
| Monitoring | support@grafana.com | Grafana/Prometheus issues |

---

## Maintenance Windows

### Standard Maintenance Window

**Schedule:** Every Sunday, 02:00-04:00 UTC

**Procedure:**

1. **Pre-Maintenance (01:45)**
   ```bash
   # Announce maintenance
   # Update status page

   # Backup everything
   ./scripts/backup.sh

   # Document current state
   docker-compose ps > pre-maintenance-state.txt
   curl http://localhost:8000/health/detailed > pre-maintenance-health.json
   ```

2. **During Maintenance (02:00-03:30)**
   ```bash
   # Apply updates
   git pull

   # Rebuild images
   docker-compose build

   # Run database migrations
   docker-compose exec web python -m alembic upgrade head

   # Update configuration
   # Review and update .env if needed

   # Restart services
   docker-compose down
   docker-compose up -d
   ```

3. **Post-Maintenance (03:30-04:00)**
   ```bash
   # Verify health
   curl http://localhost:8000/health/detailed

   # Run smoke tests
   curl -X POST http://localhost:8000/api/jobs \
     -H "X-API-Key: KEY" \
     -F "file=@test.csv"

   # Monitor for 30 minutes
   # Check logs for errors
   docker-compose logs --tail=100 web

   # Update status page
   ```

4. **Rollback Plan**
   ```bash
   # If issues detected:
   docker-compose down

   # Restore previous version
   git checkout previous-version
   docker-compose build

   # Restore database if needed
   ./scripts/restore.sh pre-maintenance-backup.sql.gz

   # Start services
   docker-compose up -d
   ```

---

## Appendix

### Useful Commands Cheat Sheet

```bash
# Quick health check
curl http://localhost:8000/health/detailed | jq .

# Count errors in last hour
docker-compose logs --since 1h web | grep -i error | wc -l

# Top 10 slowest endpoints
curl http://localhost:8000/metrics | grep duration_seconds | sort -rn | head -10

# Active connections
docker-compose exec db psql -U checker -c "SELECT count(*) FROM pg_stat_activity;"

# Disk usage by directory
du -sh gui/{uploads,exports}

# Memory usage trend
docker stats --no-stream | grep web

# Recent API keys created
docker-compose exec db psql -U checker -d website_checker -c "
  SELECT name, created_at FROM api_keys ORDER BY created_at DESC LIMIT 5;"
```

### Incident Template

```markdown
## Incident Report

**Date/Time**: YYYY-MM-DD HH:MM UTC
**Severity**: P0/P1/P2/P3
**Duration**: X minutes
**Affected Users**: Approximately X users

### Summary
Brief description of what happened.

### Timeline
- HH:MM - Incident began
- HH:MM - Alert triggered
- HH:MM - Response started
- HH:MM - Issue identified
- HH:MM - Mitigation applied
- HH:MM - Incident resolved

### Root Cause
Detailed explanation of what caused the incident.

### Resolution
Steps taken to resolve the issue.

### Impact
- User impact
- Data loss (if any)
- SLA impact

### Action Items
- [ ] Immediate fix
- [ ] Long-term prevention
- [ ] Documentation update
- [ ] Monitoring improvement

### Lessons Learned
What we learned and how to prevent similar incidents.
```

---

**Last Updated**: 2025-12-31
**Version**: 1.1.0
**Maintained By**: Operations Team
