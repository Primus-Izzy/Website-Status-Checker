# Frequently Asked Questions (FAQ)

Common questions and answers about Website Status Checker deployment and operation.

## General Questions

### What is Website Status Checker?

Website Status Checker is a production-grade application for checking the availability and status of websites at scale. It supports batch processing of thousands of URLs, provides real-time progress tracking, and includes comprehensive monitoring and alerting.

### What are the key features?

- **Batch Processing**: Process CSV/Excel files with thousands of URLs
- **Real-time Monitoring**: Live progress updates via Server-Sent Events
- **Web GUI**: FastAPI-based interface with job management
- **CLI Tool**: Command-line interface for scripting
- **Production-Ready**: Complete deployment infrastructure
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Security**: API key authentication and rate limiting
- **Auto-scaling**: Kubernetes HPA support

### What are the system requirements?

**Minimum:**
- 2 CPU cores
- 2GB RAM
- 10GB disk space
- Docker & Docker Compose

**Recommended (Production):**
- 4+ CPU cores
- 8GB RAM
- 50GB SSD
- Kubernetes cluster (for cloud deployment)

---

## Deployment Questions

### How quickly can I deploy this?

**5 minutes** with Docker Compose:
```bash
cp .env.production.example .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('ADMIN_API_KEY=' + secrets.token_hex(32))" >> .env
python -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(16))" >> .env
docker-compose up -d
docker-compose exec web python scripts/create_api_key.py --name "Initial"
```

### Can I deploy without Docker?

Yes! See `docs/DEPLOYMENT.md` for manual deployment instructions. You'll need:
- Python 3.8+
- PostgreSQL 12+ (or SQLite for development)
- Virtual environment

### Which deployment option should I choose?

| Scenario | Recommendation |
|----------|----------------|
| **Quick test/demo** | Docker Compose |
| **Small production** | Docker Compose with monitoring |
| **Enterprise/Cloud** | Kubernetes (k8s/) |
| **Development** | Manual with SQLite |

### Can I deploy to AWS/GCP/Azure?

Yes! Use the Kubernetes manifests in `k8s/`:
- **AWS EKS**: Update storage class to `gp3`
- **GCP GKE**: Update storage class to `standard-rwo`
- **Azure AKS**: Update storage class to `managed-premium`

See `k8s/README.md` for cloud-specific notes.

### Do I need Kubernetes for production?

No. Docker Compose is production-ready for:
- Small to medium deployments (< 100K requests/day)
- Single-server deployments
- Deployments where auto-scaling isn't critical

Use Kubernetes for:
- High availability requirements
- Auto-scaling needs
- Multi-region deployments
- Enterprise requirements

---

## Configuration Questions

### How do I generate secure secrets?

```bash
# SECRET_KEY (32 bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ADMIN_API_KEY (32 bytes hex)
python -c "import secrets; print(secrets.token_hex(32))"

# Database password (16 bytes)
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

Never reuse secrets across environments!

### What should ALLOWED_ORIGINS be set to?

For production, set to your actual domain(s):
```env
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**NEVER** use wildcards (`*`) in production - it's a security risk.

For development:
```env
ALLOWED_ORIGINS=http://localhost:8000,http://localhost:3000
```

### How many workers should I configure?

General rule: **2x your CPU cores**

```env
# 4 CPU cores → 8 workers
WORKERS=8

# Adjust based on workload:
# - High CPU usage → reduce workers
# - High I/O wait → increase workers
```

### How do I enable monitoring?

```bash
# Docker Compose
docker-compose --profile monitoring up -d

# Configure Grafana password in .env
GRAFANA_PASSWORD=your-secure-password

# Access Grafana at http://localhost:3000
```

---

## Database Questions

### SQLite vs PostgreSQL - which should I use?

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Production** | ❌ No | ✅ Yes |
| **Development** | ✅ Yes | ✅ Yes |
| **Concurrent users** | Limited | Unlimited |
| **Horizontal scaling** | ❌ No | ✅ Yes |
| **Backups** | File copy | pg_dump |
| **Performance** | Good | Excellent |

**Recommendation**: Use PostgreSQL for production.

### How do I backup the database?

**Docker Compose:**
```bash
# Automated
./scripts/backup.sh

# Manual
docker-compose exec db pg_dump -U checker website_checker > backup.sql
```

**Kubernetes:**
```bash
kubectl exec -n website-checker deployment/postgres -- \
  pg_dump -U checker website_checker > backup.sql
```

### How do I restore a backup?

```bash
# Docker Compose
./scripts/restore.sh backup.sql

# Kubernetes
kubectl exec -i -n website-checker deployment/postgres -- \
  psql -U checker -d website_checker < backup.sql
```

### How do I run database migrations?

```bash
# Docker Compose
docker-compose exec web python -m alembic upgrade head

# Kubernetes
kubectl exec -n website-checker deployment/website-checker -- \
  python -m alembic upgrade head

# Check current version
docker-compose exec web python -m alembic current
```

---

## Security Questions

### Is this application secure?

Yes! Security features include:
- ✅ API key authentication (database-backed)
- ✅ Rate limiting (configurable)
- ✅ CORS protection
- ✅ Security headers (HSTS, CSP, etc.)
- ✅ SSL/TLS verification
- ✅ SSRF protection
- ✅ SQL injection protection (ORM)
- ✅ File upload validation
- ✅ Secrets in environment variables
- ✅ Regular security scanning (CI/CD)

### How do I create API keys?

```bash
# Docker Compose
docker-compose exec web python scripts/create_api_key.py \
  --name "Production Key" \
  --owner-email admin@example.com \
  --rate-limit-hour 10000

# Kubernetes
kubectl exec -n website-checker deployment/website-checker -- \
  python scripts/create_api_key.py --name "Production Key"
```

### How do I rotate secrets?

1. Generate new secrets
2. Update `.env` or k8s secrets
3. Restart application
4. Update any clients using old keys

```bash
# Update .env
vim .env  # Update SECRET_KEY and ADMIN_API_KEY

# Restart
docker-compose restart web
```

### What's the default rate limit?

- **100 requests per minute** (per API key)
- **1000 requests per hour** (per API key)

Configure in `.env`:
```env
RATE_LIMIT_UPLOADS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=1000
```

---

## Monitoring Questions

### How do I access metrics?

```bash
# Prometheus format
curl http://localhost:8000/metrics

# JSON health check
curl http://localhost:8000/health/detailed | jq .
```

**Grafana Dashboard**: http://localhost:3000

### What metrics are available?

**HTTP Metrics:**
- Request count by endpoint/method/status
- Request duration (latency)
- Requests in progress

**Job Metrics:**
- Active jobs
- Job completion rate
- Processing duration

**System Metrics:**
- Memory usage
- CPU utilization
- Disk usage
- Database connections

See `docs/METRICS.md` for complete list.

### How do I configure alerts?

1. Edit `monitoring/alerts/website-checker-alerts.yml`
2. Restart Prometheus:
   ```bash
   docker-compose restart prometheus
   ```
3. Check alerts: http://localhost:9090/alerts

For notifications, configure Alertmanager (see `monitoring/README.md`).

### Why am I getting so many alerts?

**Alert fatigue solutions:**
1. Adjust thresholds in `monitoring/alerts/*.yml`
2. Increase `for:` duration
3. Disable non-actionable alerts
4. Review weekly and tune

Example:
```yaml
# Too sensitive
expr: cpu_percent > 50
for: 1m

# Better
expr: cpu_percent > 80
for: 5m
```

---

## Performance Questions

### How many concurrent jobs can it handle?

**Default**: 10 concurrent jobs

Configure in `.env`:
```env
MAX_CONCURRENT_JOBS=20
```

**Factors affecting capacity:**
- CPU cores
- Memory available
- Network bandwidth
- Target website response times

### How do I improve performance?

**1. Scale Horizontally**
```bash
# Docker Compose
docker-compose up -d --scale web=5

# Kubernetes (automatic with HPA)
kubectl scale deployment website-checker -n website-checker --replicas=5
```

**2. Optimize Workers**
```env
WORKERS=8  # 2x CPU cores
```

**3. Increase Resources**
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
```

**4. Database Optimization**
- Add indexes
- Increase connection pool
- Run cleanup regularly

### What's the maximum file size for uploads?

**Default**: 100MB

Configure in `.env`:
```env
MAX_UPLOAD_SIZE_MB=200
```

Also update reverse proxy (nginx, etc.):
```nginx
client_max_body_size 200M;
```

### How many URLs can I process in one batch?

**Tested up to**: 100,000 URLs per batch

**Performance by batch size:**
- 1,000 URLs: ~1-2 minutes
- 10,000 URLs: ~10-20 minutes
- 100,000 URLs: ~2-3 hours

**Tips for large batches:**
- Use concurrent processing
- Monitor memory usage
- Consider splitting very large files

---

## Operational Questions

### How do I update the application?

```bash
# 1. Backup first
./scripts/backup.sh

# 2. Pull latest code
git pull

# 3. Rebuild and restart
docker-compose build
docker-compose down
docker-compose up -d

# 4. Run migrations
docker-compose exec web python -m alembic upgrade head
```

See `RUNBOOK.md` for maintenance procedures.

### How do I check if it's working?

```bash
# Quick health check
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed | jq .

# Run health check script
./scripts/health_check.sh
```

Expected: All checks return `"healthy"` or `200 OK`.

### How do I clean up old data?

**Automated:**
```bash
# Clean files older than 24 hours (default)
./scripts/cleanup.sh

# Clean files older than 48 hours
./scripts/cleanup.sh 48
```

**Manual:**
```bash
# Files
find gui/uploads -type f -mtime +1 -delete
find gui/exports -type f -mtime +1 -delete

# Database (via Docker)
docker-compose exec db psql -U checker -d website_checker -c "
  DELETE FROM jobs WHERE created_at < NOW() - INTERVAL '24 hours';"
```

### What should I monitor daily?

Use `QUICK_REFERENCE.md` daily checklist:
1. Health endpoint status
2. Active alerts (should be 0)
3. Resource usage (<80%)
4. Backup completion
5. Error log count

### Where are the logs?

**Docker Compose:**
```bash
# Application logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f
```

**Kubernetes:**
```bash
kubectl logs -n website-checker -l app=website-checker --tail=100 -f
```

**Log files** (if configured):
```bash
tail -f logs/app.log
```

---

## Troubleshooting Questions

### Services won't start

**Check:**
1. `.env` file exists and has required variables
2. Ports not already in use
3. Docker daemon running
4. Sufficient disk space

```bash
# Diagnose
docker-compose config  # Validate config
docker-compose logs     # Check errors
df -h                   # Check disk space
```

### "Database connection failed"

**Solutions:**
```bash
# Check database status
docker-compose exec db pg_isready

# Restart database
docker-compose restart db

# Check DATABASE_URL in .env
grep DATABASE_URL .env

# Test connection
docker-compose exec web python -c "
from gui.database.session import engine
engine.connect()
print('Connection successful!')
"
```

### "API key authentication failed"

**Solutions:**
```bash
# Create new API key
docker-compose exec web python scripts/create_api_key.py --name "Test"

# List existing keys (requires admin key)
curl "http://localhost:8000/api/admin/api-keys?admin_key=YOUR_ADMIN_KEY"

# Verify key format
# Should be: wsc_[40 alphanumeric characters]
```

### High memory usage

**Investigate:**
```bash
# Check usage
docker stats --no-stream

# Check active jobs
curl http://localhost:8000/health/detailed | jq '.metrics.active_jobs'

# Check for leaks
# Memory steadily increasing = possible leak
```

**Solutions:**
1. Restart service: `docker-compose restart web`
2. Reduce concurrent jobs: Edit `MAX_CONCURRENT_JOBS` in `.env`
3. Clean up old data: `./scripts/cleanup.sh`
4. Increase resources: Edit `docker-compose.yml`

### Jobs stuck in "processing"

**Solutions:**
```bash
# Restart workers
docker-compose restart web

# Check job status in database
docker-compose exec db psql -U checker -d website_checker -c "
  SELECT id, status, created_at, updated_at
  FROM jobs
  WHERE status = 'processing'
  ORDER BY updated_at DESC;"

# Manually mark as failed (if truly stuck)
docker-compose exec db psql -U checker -d website_checker -c "
  UPDATE jobs
  SET status = 'failed', error_message = 'Timeout - manually reset'
  WHERE status = 'processing' AND updated_at < NOW() - INTERVAL '2 hours';"
```

---

## Integration Questions

### Can I use this programmatically?

Yes! Use the REST API:

```python
import requests

# Upload file
url = "http://localhost:8000/api/jobs"
headers = {"X-API-Key": "your-api-key"}
files = {"file": open("urls.csv", "rb")}

response = requests.post(url, headers=headers, files=files)
job = response.json()

# Check status
status_url = f"http://localhost:8000/api/jobs/{job['id']}"
status = requests.get(status_url, headers=headers).json()

# Download results
results_url = f"http://localhost:8000/api/jobs/{job['id']}/export?format=json"
results = requests.get(results_url, headers=headers).json()
```

### Does it have a Python SDK?

Not yet, but the API is RESTful and well-documented at `/api/docs` (when `ENV=development`).

### Can I integrate with my monitoring stack?

Yes! Supports:
- **Prometheus**: Scrape `/metrics` endpoint
- **Datadog**: Use Datadog agent with Prometheus integration
- **New Relic**: Use Prometheus remote write
- **Grafana Cloud**: Configure remote write
- **Sentry**: Set `SENTRY_DSN` in `.env`

### Can I run this in CI/CD?

Yes! Use the CLI:

```bash
# In your CI pipeline
docker run -v $(pwd):/data website-status-checker \
  python src/cli/main.py /data/urls.csv -o /data/results.csv --active-only
```

---

## Scaling Questions

### How do I scale horizontally?

**Docker Compose:**
```bash
docker-compose up -d --scale web=5
```

**Kubernetes:**
```bash
# Manual
kubectl scale deployment website-checker -n website-checker --replicas=5

# Automatic (HPA already configured)
kubectl apply -f k8s/hpa.yaml
```

**Requirements for horizontal scaling:**
- PostgreSQL (not SQLite)
- Shared storage for uploads/exports
- Load balancer

### What's the maximum scale?

**Tested limits:**
- 10 application instances (Docker Compose)
- 50+ pods (Kubernetes with HPA)
- 100K+ requests per hour
- 1M+ URLs processed per day

**Bottlenecks:**
- Database connections
- Network bandwidth
- Storage I/O

### Do I need a load balancer?

**Docker Compose**: Not required (Docker handles routing)

**Kubernetes**: Automatically provided by Service/Ingress

**Manual deployment**: Yes, use nginx or similar

---

## Cost Questions

### How much does it cost to run?

**Infrastructure costs** (example):

| Platform | Configuration | Monthly Cost |
|----------|--------------|--------------|
| **AWS** | t3.medium (2 vCPU, 4GB) | ~$30 |
| **GCP** | e2-medium (2 vCPU, 4GB) | ~$25 |
| **Azure** | B2s (2 vCPU, 4GB) | ~$30 |
| **DigitalOcean** | 2 vCPU, 4GB | ~$24 |
| **On-premise** | Own hardware | $0 |

**Plus:**
- Database storage: ~$10/month (100GB)
- Bandwidth: Varies by usage
- Monitoring (optional): $0-50/month

### Is there a free tier option?

Yes! Use:
- **Docker Compose** on your own server
- **Free cloud tiers**: AWS Free Tier, GCP Free Tier
- **Local development**: Completely free

### What are the main cost drivers?

1. **Compute**: CPU/memory for workers
2. **Storage**: Database and file storage
3. **Bandwidth**: Outbound traffic
4. **Monitoring**: Grafana Cloud, Datadog, etc. (optional)

**Cost optimization:**
- Use auto-scaling (pay for what you use)
- Clean up old data regularly
- Use spot instances (AWS, GCP)
- Optimize worker count

---

## Support Questions

### Where can I get help?

1. **Documentation**: Check the docs/ directory
2. **Runbook**: See RUNBOOK.md for common issues
3. **Quick Reference**: See QUICK_REFERENCE.md
4. **GitHub Issues**: Report bugs or ask questions
5. **Community**: (Add your community links here)

### How do I report a bug?

1. Check if it's a known issue in GitHub
2. Gather information:
   - Error messages
   - Logs: `docker-compose logs`
   - Configuration (without secrets!)
   - Steps to reproduce
3. Open GitHub issue with details

### How do I request a feature?

Open a GitHub issue with:
- Use case description
- Expected behavior
- Why it's valuable
- Proposed implementation (optional)

### Is there commercial support?

(Update with your support options)

---

## License Questions

### What license is this under?

(Update with your license - MIT, Apache 2.0, etc.)

### Can I use this commercially?

(Update based on your license)

### Can I modify the code?

(Update based on your license)

---

## Contributing Questions

### How can I contribute?

See CONTRIBUTING.md (if you create one) or:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### What are the contribution guidelines?

- Follow existing code style
- Add tests for new features
- Update documentation
- Follow commit message format
- Pass CI/CD checks

---

**Last Updated**: 2025-12-31
**Version**: 1.1.0

**Didn't find your question?** Open a GitHub issue or check the documentation:
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- [RUNBOOK.md](RUNBOOK.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
