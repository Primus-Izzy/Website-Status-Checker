# Quick Reference Guide

One-page reference for common operations and commands.

## 🚀 Quick Deploy

```bash
cp .env.production.example .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('ADMIN_API_KEY=' + secrets.token_hex(32))" >> .env
python -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(16))" >> .env
docker-compose up -d
docker-compose exec web python scripts/create_api_key.py --name "Production"
```

## 📍 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Application | http://localhost:8000 | Main web interface |
| Health Check | http://localhost:8000/health/detailed | System health |
| Metrics | http://localhost:8000/metrics | Prometheus metrics |
| Prometheus | http://localhost:9090 | Metrics & alerts |
| Grafana | http://localhost:3000 | Dashboards |

## 🔧 Common Commands

### Docker Compose

```bash
# Start all services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f web
docker-compose logs -f db

# Restart service
docker-compose restart web

# Check status
docker-compose ps
```

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed | jq .

# Liveness probe (Kubernetes)
curl http://localhost:8000/health/live

# Readiness probe (Kubernetes)
curl http://localhost:8000/health/ready

# Run health check script
./scripts/health_check.sh
# Windows: scripts\health_check.bat
```

### Database

```bash
# Run migrations
docker-compose exec web python -m alembic upgrade head

# Check current migration
docker-compose exec web python -m alembic current

# Backup database
./scripts/backup.sh
docker-compose exec db pg_dump -U checker website_checker > backup.sql

# Restore database
./scripts/restore.sh backup.sql
docker-compose exec -T db psql -U checker website_checker < backup.sql

# Access database shell
docker-compose exec db psql -U checker -d website_checker

# Check database status
docker-compose exec db pg_isready
```

### API Keys

```bash
# Create API key
docker-compose exec web python scripts/create_api_key.py --name "My Key"

# Create with options
docker-compose exec web python scripts/create_api_key.py \
  --name "Production Key" \
  --owner-email admin@example.com \
  --rate-limit-hour 10000

# List API keys (requires admin key)
curl "http://localhost:8000/api/admin/api-keys?admin_key=YOUR_ADMIN_KEY"
```

### Cleanup

```bash
# Clean old files (24 hours)
./scripts/cleanup.sh

# Clean files older than 48 hours
./scripts/cleanup.sh 48

# Manual cleanup
find gui/uploads -type f -mtime +1 -delete
find gui/exports -type f -mtime +1 -delete
```

### Monitoring

```bash
# View metrics
curl http://localhost:8000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check active alerts
curl http://localhost:9090/api/v1/alerts

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=up'
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check .env file
cat .env | grep -E "SECRET_KEY|ADMIN_API_KEY|DB_PASSWORD"

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Failed

```bash
# Check database status
docker-compose exec db pg_isready

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Can't Access Web Interface

```bash
# Check if running
docker-compose ps web

# Check logs
docker-compose logs web

# Test from inside container
docker-compose exec web curl http://localhost:8000/health
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Check application metrics
curl http://localhost:8000/health/detailed | jq '.metrics'

# Restart service
docker-compose restart web
```

## 📊 Metrics Quick Reference

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `up` | Service availability | 0 for >2min |
| `http_requests_total` | Total HTTP requests | Error rate >5% |
| `http_request_duration_seconds` | Request latency | P95 >2s |
| `active_jobs` | Currently active jobs | >8 for >10min |
| `database_connections` | DB connection pool | >90% for >2min |
| `memory_usage_bytes` | Memory usage | >3GB for >5min |
| `cpu_percent` | CPU utilization | >80% for >5min |

## 🔐 Security Checklist

- [ ] Strong SECRET_KEY generated
- [ ] Strong ADMIN_API_KEY generated
- [ ] Database password is secure
- [ ] ALLOWED_ORIGINS configured (no wildcards!)
- [ ] SSL_VERIFY_DEFAULT=true
- [ ] RATE_LIMIT_ENABLED=true
- [ ] ENABLE_SECURITY_HEADERS=true
- [ ] ENV=production
- [ ] DEBUG=false
- [ ] Firewall configured
- [ ] SSL/TLS enabled
- [ ] Backups scheduled

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | Environment configuration |
| `docker-compose.yml` | Service orchestration |
| `Dockerfile` | Container image definition |
| `alembic.ini` | Database migrations config |
| `monitoring/prometheus.yml` | Metrics collection config |
| `monitoring/alerts/*.yml` | Alert rules |

## 🔄 Update & Maintenance

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose down
docker-compose up -d

# Run migrations
docker-compose exec web python -m alembic upgrade head
```

### Backup Strategy

```bash
# Daily backup (add to cron)
0 2 * * * /path/to/scripts/backup.sh

# Weekly cleanup
0 3 * * 0 /path/to/scripts/cleanup.sh 168
```

### Log Management

```bash
# View recent logs
docker-compose logs --tail=100 web

# Follow logs
docker-compose logs -f web

# Export logs
docker-compose logs web > web.log

# JSON logs for analysis
docker-compose logs web | jq .
```

## 🎯 Performance Tuning

### For High Load

```env
# .env adjustments
WORKERS=8  # 2x CPU cores
MAX_CONCURRENT_JOBS=20
DATABASE_URL=postgresql://...?pool_size=20&max_overflow=40
```

### For Limited Resources

```env
# .env adjustments
WORKERS=2
MAX_CONCURRENT_JOBS=5
JOB_RETENTION_HOURS=12
```

## 📞 Emergency Contacts

```bash
# Application logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db

# System metrics
curl http://localhost:8000/health/detailed

# Prometheus alerts
curl http://localhost:9090/api/v1/alerts

# Restart everything
docker-compose restart
```

## 🔗 Documentation Links

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview |
| [DOCKER_README.md](DOCKER_README.md) | Quick deployment |
| [PRODUCTION_READY.md](PRODUCTION_READY.md) | Production checklist |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Full deployment guide |
| [docs/METRICS.md](docs/METRICS.md) | Metrics documentation |
| [monitoring/README.md](monitoring/README.md) | Monitoring guide |
| [k8s/README.md](k8s/README.md) | Kubernetes deployment |
| [scripts/README.md](scripts/README.md) | Operations scripts |

## 💡 Pro Tips

1. **Always check health endpoint first** when troubleshooting
2. **Use structured logs** (LOG_FORMAT=json) for production
3. **Monitor disk space** - old exports can accumulate
4. **Test backups regularly** - restore to verify
5. **Review Prometheus alerts** weekly to reduce noise
6. **Scale horizontally** with docker-compose or Kubernetes
7. **Use cleanup script** in cron for automated maintenance
8. **Keep secrets in .env** - never commit to Git
9. **Monitor memory trends** - catch leaks early
10. **Document incidents** - build your runbook

---

**Last Updated**: 2025-12-31
**Version**: 1.1.0
**Support**: Check documentation or open GitHub issue
