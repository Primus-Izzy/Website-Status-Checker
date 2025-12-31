# Disaster Recovery Plan

Procedures for recovering from catastrophic failures of the Website Status Checker system.

## Overview

**Recovery Time Objective (RTO)**: 15 minutes
**Recovery Point Objective (RPO)**: 24 hours
**Last Updated**: 2025-12-31
**Version**: 1.1.0

---

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Disaster Scenarios](#disaster-scenarios)
3. [Recovery Procedures](#recovery-procedures)
4. [Verification Steps](#verification-steps)
5. [Post-Recovery Actions](#post-recovery-actions)
6. [Testing the DR Plan](#testing-the-dr-plan)

---

## Backup Strategy

### What Gets Backed Up

| Component | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| **Database** | Daily (02:00 UTC) | 30 days | `backups/` + S3/GCS |
| **Configuration** | On change | Version control | Git repository |
| **Uploaded Files** | Daily | 7 days | Persistent volume |
| **Exported Files** | Daily | 7 days | Persistent volume |
| **Secrets** | Manual | Secure vault | KMS/Vault |
| **Logs** | Continuous | 30 days | Log aggregation service |

### Automated Backup Schedule

**Cron Configuration:**
```bash
# Daily database backup at 02:00 UTC
0 2 * * * /path/to/scripts/backup.sh

# Weekly full backup Sunday at 03:00 UTC
0 3 * * 0 /path/to/scripts/full_backup.sh

# Monthly backup retention cleanup
0 4 1 * * find /backups -name "*.sql.gz" -mtime +30 -delete
```

### Backup Locations

**Primary**: Local server (`./backups/`)
**Secondary**: Cloud storage (S3, GCS, Azure Blob)
**Tertiary**: Off-site backup server

**Cloud Sync Example:**
```bash
# Sync to S3 (add to backup script)
aws s3 sync ./backups/ s3://your-bucket/website-checker-backups/ \
  --storage-class STANDARD_IA

# Sync to Google Cloud Storage
gsutil rsync -r ./backups/ gs://your-bucket/website-checker-backups/
```

---

## Disaster Scenarios

### Scenario 1: Application Failure

**Symptoms:**
- Application pods/containers crashing
- Health checks failing
- 502/503 errors

**Impact:** High - Service unavailable
**Recovery Time:** 5-10 minutes

### Scenario 2: Database Corruption

**Symptoms:**
- Database connection errors
- Data integrity errors
- Corrupted index errors

**Impact:** Critical - Data loss risk
**Recovery Time:** 15-30 minutes

### Scenario 3: Complete Server Loss

**Symptoms:**
- Server unreachable
- All services down
- Hardware failure

**Impact:** Critical - Complete outage
**Recovery Time:** 30-60 minutes

### Scenario 4: Data Center Outage

**Symptoms:**
- Multiple servers unreachable
- Network partition
- Infrastructure failure

**Impact:** Critical - Complete outage
**Recovery Time:** 1-4 hours

### Scenario 5: Accidental Data Deletion

**Symptoms:**
- Missing database records
- Deleted files
- User reports data loss

**Impact:** Medium - Partial data loss
**Recovery Time:** 10-20 minutes

### Scenario 6: Security Breach

**Symptoms:**
- Unauthorized access detected
- Compromised credentials
- Malicious activity

**Impact:** Critical - Security incident
**Recovery Time:** 2-8 hours

---

## Recovery Procedures

### Procedure 1: Application Failure Recovery

**When to Use:** Application crashes, high error rate, but database intact

**Steps:**

1. **Assess Situation** (1 minute)
   ```bash
   # Check service status
   docker-compose ps
   # OR
   kubectl get pods -n website-checker

   # Check recent logs
   docker-compose logs --tail=50 web
   ```

2. **Quick Restart** (2 minutes)
   ```bash
   # Docker Compose
   docker-compose restart web

   # Kubernetes
   kubectl rollout restart deployment/website-checker -n website-checker
   ```

3. **If Restart Fails, Rebuild** (5 minutes)
   ```bash
   # Docker Compose
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d

   # Kubernetes
   kubectl delete pods -n website-checker -l app=website-checker
   ```

4. **Verify Recovery** (2 minutes)
   ```bash
   # Check health
   curl http://localhost:8000/health/detailed

   # Check metrics
   curl http://localhost:8000/metrics | grep up

   # Test functionality
   curl -X GET http://localhost:8000/api/admin/status \
     -H "X-API-Key: YOUR_KEY"
   ```

**Total Time:** ~10 minutes

### Procedure 2: Database Corruption Recovery

**When to Use:** Database errors, corrupted data, index issues

**Steps:**

1. **Stop Application** (1 minute)
   ```bash
   # Prevent further writes
   docker-compose stop web
   # OR
   kubectl scale deployment website-checker -n website-checker --replicas=0
   ```

2. **Assess Database** (2 minutes)
   ```bash
   # Check database status
   docker-compose exec db pg_isready

   # Check for corruption
   docker-compose exec db psql -U checker -d website_checker -c "
     SELECT pg_database.datname,
            pg_size_pretty(pg_database_size(pg_database.datname)) AS size
     FROM pg_database;"

   # Check table integrity
   docker-compose exec db psql -U checker -d website_checker -c "
     ANALYZE;
     REINDEX DATABASE website_checker;"
   ```

3. **Restore from Latest Backup** (10 minutes)
   ```bash
   # Find latest backup
   ls -lht backups/ | head -5

   # Restore database
   ./scripts/restore.sh backups/latest_backup.sql.gz
   ```

4. **Verify Data Integrity** (3 minutes)
   ```bash
   # Check record counts
   docker-compose exec db psql -U checker -d website_checker -c "
     SELECT 'jobs' as table_name, COUNT(*) FROM jobs
     UNION ALL
     SELECT 'url_check_results', COUNT(*) FROM url_check_results
     UNION ALL
     SELECT 'api_keys', COUNT(*) FROM api_keys;"

   # Check for recent data
   docker-compose exec db psql -U checker -d website_checker -c "
     SELECT MAX(created_at) as latest_job FROM jobs;"
   ```

5. **Restart Application** (2 minutes)
   ```bash
   # Docker Compose
   docker-compose start web

   # Kubernetes
   kubectl scale deployment website-checker -n website-checker --replicas=3
   ```

**Total Time:** ~18 minutes
**Data Loss:** Up to 24 hours (last backup)

### Procedure 3: Complete Server Loss Recovery

**When to Use:** Hardware failure, server destroyed, complete loss

**Prerequisites:**
- Access to backups (cloud storage)
- New server/VM provisioned
- Domain DNS can be updated

**Steps:**

1. **Provision New Server** (10 minutes)
   ```bash
   # On new server
   # Install Docker
   curl -fsSL https://get.docker.com | sh

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
     -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Clone Repository** (2 minutes)
   ```bash
   git clone https://github.com/your-org/website-status-checker.git
   cd website-status-checker
   ```

3. **Restore Configuration** (3 minutes)
   ```bash
   # Retrieve secrets from vault/KMS
   # Create .env file
   cp .env.production.example .env

   # Populate from secure storage
   # Or manually set:
   # SECRET_KEY=...
   # ADMIN_API_KEY=...
   # DB_PASSWORD=...
   # ALLOWED_ORIGINS=...
   ```

4. **Download Latest Backup** (5 minutes)
   ```bash
   # From S3
   aws s3 cp s3://your-bucket/website-checker-backups/latest_backup.sql.gz ./backups/

   # From GCS
   gsutil cp gs://your-bucket/website-checker-backups/latest_backup.sql.gz ./backups/
   ```

5. **Start Services** (5 minutes)
   ```bash
   # Start database first
   docker-compose up -d db

   # Wait for database
   sleep 30

   # Restore data
   ./scripts/restore.sh backups/latest_backup.sql.gz

   # Start application
   docker-compose up -d
   ```

6. **Create API Keys** (2 minutes)
   ```bash
   # Recreate production API keys
   docker-compose exec web python scripts/create_api_key.py \
     --name "Production Key" \
     --owner-email admin@example.com
   ```

7. **Update DNS** (5 minutes - propagation time varies)
   ```bash
   # Point domain to new server IP
   # Update A/CNAME records
   ```

8. **Verify and Monitor** (10 minutes)
   ```bash
   # Check all services
   docker-compose ps

   # Health check
   curl https://yourdomain.com/health/detailed

   # Monitor logs
   docker-compose logs -f web
   ```

**Total Time:** ~42 minutes (excluding DNS propagation)
**Data Loss:** Up to 24 hours

### Procedure 4: Kubernetes Cluster Recovery

**When to Use:** K8s cluster failure, need to restore to new cluster

**Steps:**

1. **Provision New Cluster** (15 minutes)
   ```bash
   # AWS EKS
   eksctl create cluster --name website-checker-recovery \
     --region us-east-1 --nodes 3

   # GCP GKE
   gcloud container clusters create website-checker-recovery \
     --zone us-central1-a --num-nodes 3
   ```

2. **Configure kubectl** (1 minute)
   ```bash
   # AWS
   aws eks update-kubeconfig --name website-checker-recovery --region us-east-1

   # GCP
   gcloud container clusters get-credentials website-checker-recovery --zone us-central1-a
   ```

3. **Deploy Infrastructure** (5 minutes)
   ```bash
   cd k8s/

   # Create namespace
   kubectl apply -f namespace.yaml

   # Update secrets.yaml with actual values
   vim secrets.yaml

   # Apply secrets and config
   kubectl apply -f secrets.yaml
   kubectl apply -f configmap.yaml
   ```

4. **Deploy Database** (5 minutes)
   ```bash
   # Deploy PostgreSQL
   kubectl apply -f postgres-deployment.yaml

   # Wait for database
   kubectl wait --for=condition=ready pod -l app=postgres \
     -n website-checker --timeout=300s
   ```

5. **Restore Database** (10 minutes)
   ```bash
   # Download backup
   aws s3 cp s3://your-bucket/website-checker-backups/latest_backup.sql.gz ./

   # Copy to pod
   kubectl cp latest_backup.sql.gz \
     website-checker/postgres-pod-name:/tmp/backup.sql.gz

   # Restore
   kubectl exec -n website-checker deployment/postgres -- \
     bash -c "gunzip < /tmp/backup.sql.gz | psql -U checker -d website_checker"
   ```

6. **Deploy Application** (5 minutes)
   ```bash
   # Deploy app
   kubectl apply -f app-deployment.yaml
   kubectl apply -f ingress.yaml
   kubectl apply -f hpa.yaml

   # Wait for pods
   kubectl wait --for=condition=ready pod -l app=website-checker \
     -n website-checker --timeout=300s
   ```

7. **Verify** (5 minutes)
   ```bash
   # Check pods
   kubectl get pods -n website-checker

   # Check ingress
   kubectl get ingress -n website-checker

   # Test health
   kubectl port-forward -n website-checker svc/website-checker 8000:8000
   curl http://localhost:8000/health/detailed
   ```

**Total Time:** ~46 minutes
**Data Loss:** Up to 24 hours

### Procedure 5: Accidental Data Deletion Recovery

**When to Use:** Accidental DELETE, TRUNCATE, or DROP

**Steps:**

1. **Immediately Stop Application** (<1 minute)
   ```bash
   # Prevent further changes
   docker-compose stop web
   ```

2. **Identify Deletion Time** (2 minutes)
   ```bash
   # Check application logs for DELETE statements
   docker-compose logs web | grep -i "delete\|truncate\|drop"

   # Check database logs
   docker-compose exec db cat /var/log/postgresql/postgresql.log | tail -100
   ```

3. **Find Point-in-Time Backup** (3 minutes)
   ```bash
   # List backups around deletion time
   ls -lht backups/ | head -10

   # Find backup BEFORE deletion
   # Example: deletion at 14:30, use backup from 02:00 (last night)
   ```

4. **Restore to Temporary Database** (10 minutes)
   ```bash
   # Create temp database
   docker-compose exec db psql -U checker -c "CREATE DATABASE temp_recovery;"

   # Restore to temp
   gunzip < backups/backup_before_deletion.sql.gz | \
     docker-compose exec -T db psql -U checker -d temp_recovery
   ```

5. **Extract Missing Data** (5 minutes)
   ```bash
   # Export missing records
   docker-compose exec db psql -U checker -d temp_recovery -c "
     COPY (SELECT * FROM jobs WHERE id IN (1,2,3...))
     TO '/tmp/missing_jobs.csv' WITH CSV HEADER;"

   # Copy file out
   docker cp $(docker-compose ps -q db):/tmp/missing_jobs.csv ./
   ```

6. **Import to Production** (3 minutes)
   ```bash
   # Import missing data
   docker-compose exec -T db psql -U checker -d website_checker -c "
     COPY jobs FROM '/tmp/missing_jobs.csv' WITH CSV HEADER;"
   ```

7. **Verify and Restart** (2 minutes)
   ```bash
   # Verify data restored
   docker-compose exec db psql -U checker -d website_checker -c "
     SELECT COUNT(*) FROM jobs WHERE id IN (1,2,3...);"

   # Drop temp database
   docker-compose exec db psql -U checker -c "DROP DATABASE temp_recovery;"

   # Restart application
   docker-compose start web
   ```

**Total Time:** ~25 minutes
**Data Loss:** Minimal (only changes since last backup)

---

## Verification Steps

After any recovery, perform these checks:

### 1. Service Health

```bash
# Basic health
curl https://yourdomain.com/health

# Detailed health with metrics
curl https://yourdomain.com/health/detailed | jq .

# Expected: status = "healthy"
```

### 2. Database Connectivity

```bash
# Check connection
docker-compose exec web python -c "
from gui.database.session import engine
conn = engine.connect()
print('Database connected successfully!')
conn.close()
"

# Check record counts
docker-compose exec db psql -U checker -d website_checker -c "
  SELECT 'jobs' as table, COUNT(*) as count FROM jobs
  UNION ALL
  SELECT 'url_check_results', COUNT(*) FROM url_check_results
  UNION ALL
  SELECT 'api_keys', COUNT(*) FROM api_keys;"
```

### 3. API Functionality

```bash
# Test API with real request
curl -X GET "https://yourdomain.com/api/admin/status" \
  -H "X-API-Key: YOUR_API_KEY"

# Expected: {"status": "ok", ...}
```

### 4. File Operations

```bash
# Check upload/export directories
ls -lah gui/uploads gui/exports

# Test file upload
curl -X POST "https://yourdomain.com/api/jobs" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@test_urls.csv"
```

### 5. Monitoring

```bash
# Check Prometheus metrics
curl https://yourdomain.com/metrics | grep "^up "

# Check no active alerts
curl http://prometheus:9090/api/v1/alerts | jq '.data.alerts | length'

# Expected: 0 alerts
```

### 6. Data Integrity

```bash
# Spot check recent data
docker-compose exec db psql -U checker -d website_checker -c "
  SELECT id, status, created_at
  FROM jobs
  ORDER BY created_at DESC
  LIMIT 5;"

# Check for orphaned records
docker-compose exec db psql -U checker -d website_checker -c "
  SELECT COUNT(*) as orphaned_results
  FROM url_check_results ucr
  LEFT JOIN jobs j ON ucr.job_id = j.id
  WHERE j.id IS NULL;"

# Expected: 0 orphaned records
```

---

## Post-Recovery Actions

### Immediate (Within 1 hour)

1. **Notify Stakeholders**
   - Send recovery status update
   - Document data loss (if any)
   - Provide ETA for full functionality

2. **Monitor Closely**
   - Watch error rates
   - Monitor resource usage
   - Check for anomalies

3. **Document Incident**
   - What happened
   - Root cause
   - Recovery steps taken
   - Lessons learned

### Short-term (Within 24 hours)

1. **Verify Backups**
   - Test latest backup
   - Confirm backup process working
   - Check backup retention

2. **Review Logs**
   - Analyze logs leading to incident
   - Check for warnings missed
   - Update alert thresholds if needed

3. **Update Documentation**
   - Update runbook with new learnings
   - Document any process changes
   - Update DR plan if needed

### Long-term (Within 1 week)

1. **Root Cause Analysis**
   - Detailed incident report
   - Timeline of events
   - Contributing factors
   - Prevention measures

2. **Implement Improvements**
   - Fix identified issues
   - Add monitoring/alerting
   - Improve automation

3. **Team Review**
   - Share lessons learned
   - Update procedures
   - Train team on changes

---

## Testing the DR Plan

### Monthly DR Test

**Schedule:** Last Sunday of each month, 06:00 UTC

**Procedure:**

1. **Announce Test** (Day before)
   - Notify team
   - Schedule maintenance window
   - Prepare test environment

2. **Execute Test** (2 hours)
   ```bash
   # 1. Create fresh backup
   ./scripts/backup.sh

   # 2. Provision test environment
   # Use separate docker-compose or k8s namespace

   # 3. Restore backup to test environment
   ./scripts/restore.sh latest_backup.sql.gz

   # 4. Run verification steps
   ./scripts/health_check.sh

   # 5. Document results
   # - Recovery time
   # - Issues encountered
   # - Improvements needed
   ```

3. **Review Results** (30 minutes)
   - Compare to RTO/RPO targets
   - Identify gaps
   - Update procedures

4. **Update DR Plan** (As needed)
   - Document changes
   - Update version
   - Communicate updates

### Annual Full DR Drill

**Schedule:** Annually

**Scope:** Complete infrastructure recovery simulation

---

## Emergency Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| **On-Call Engineer** | Check PagerDuty | 24/7 |
| **Database Admin** | (Contact info) | Business hours |
| **Security Team** | (Contact info) | 24/7 for incidents |
| **Cloud Provider Support** | AWS/GCP/Azure support | 24/7 |

---

## Appendix

### Backup Script Reference

```bash
# Location
./scripts/backup.sh

# Usage
./scripts/backup.sh [backup_directory]

# Default
./scripts/backup.sh  # Saves to ./backups/
```

### Restore Script Reference

```bash
# Location
./scripts/restore.sh

# Usage
./scripts/restore.sh <backup_file>

# Example
./scripts/restore.sh ./backups/website_checker_20250131_020000.sql.gz
```

### Critical File Locations

| File/Directory | Purpose | Backup Priority |
|----------------|---------|-----------------|
| `.env` | Configuration | Critical |
| `backups/` | Database backups | Critical |
| `gui/uploads/` | Uploaded files | High |
| `gui/exports/` | Export files | Medium |
| `docker-compose.yml` | Service config | Medium (in Git) |
| `k8s/` | K8s manifests | Medium (in Git) |

---

**Last Tested**: (Update after each DR test)
**Next Test**: (Schedule next test)
**Plan Version**: 1.1.0
**Owner**: Operations Team

**Remember**: The best disaster recovery is disaster prevention. Keep backups current, monitor proactively, and test regularly!
