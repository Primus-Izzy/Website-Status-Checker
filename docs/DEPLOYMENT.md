# Deployment Guide
**Website Status Checker - Production Deployment**

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Docker Deployment](#docker-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Production Checklist](#production-checklist)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Docker & Docker Compose (recommended)
- OR Python 3.8+ (for manual deployment)
- PostgreSQL 12+ (production) or SQLite (development)
- 2GB+ RAM, 2+ CPU cores recommended

### 1-Minute Docker Deploy
```bash
# 1. Clone repository
git clone https://github.com/your-org/website-status-checker.git
cd website-status-checker

# 2. Copy and configure environment
cp .env.production.example .env

# 3. Generate secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('ADMIN_API_KEY=' + secrets.token_hex(32))" >> .env
python -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(16))" >> .env

# 4. Set your domain
sed -i 's/ALLOWED_ORIGINS=.*/ALLOWED_ORIGINS=https://yourdomain.com/' .env

# 5. Launch
docker-compose up -d

# 6. Create first API key
docker-compose exec web python scripts/create_api_key.py --name "Production Key"

# Done! Access at http://localhost:8000
```

---

## Docker Deployment

### Option 1: Docker Compose (Recommended)

#### Full Stack (Web + PostgreSQL)
```bash
docker-compose up -d
```

#### With Monitoring (Prometheus + Grafana)
```bash
docker-compose --profile monitoring up -d
```

#### Services:
- **web**: Main application (port 8000)
- **db**: PostgreSQL database (port 5432)
- **prometheus**: Metrics collector (port 9090) - optional
- **grafana**: Metrics visualization (port 3000) - optional

#### Check Status:
```bash
# View logs
docker-compose logs -f web

# Check health
curl http://localhost:8000/health

# Check database
docker-compose exec db psql -U checker -d website_checker -c "SELECT COUNT(*) FROM jobs;"
```

### Option 2: Docker Only (Single Container)

```bash
# Build image
docker build -t website-status-checker .

# Run with SQLite (development)
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/gui/uploads:/app/gui/uploads \
  -v $(pwd)/gui/exports:/app/gui/exports \
  --env-file .env \
  --name website-checker \
  website-status-checker

# Run with external PostgreSQL (production)
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/dbname \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_API_KEY=your-admin-key \
  -v $(pwd)/gui/uploads:/app/gui/uploads \
  -v $(pwd)/gui/exports:/app/gui/exports \
  --name website-checker \
  website-status-checker
```

---

## Manual Deployment

### System Requirements
- Python 3.8, 3.9, 3.10, 3.11, or 3.12
- PostgreSQL 12+ (or SQLite for testing)
- 2GB+ RAM
- Linux, macOS, or Windows

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-gui.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ADMIN_API_KEY=' + secrets.token_hex(32))"

# Edit .env and set:
# - SECRET_KEY
# - ADMIN_API_KEY
# - DATABASE_URL (for PostgreSQL)
# - ALLOWED_ORIGINS (your domain)
```

### Step 3: Database Setup

#### PostgreSQL (Production):
```bash
# Create database
createdb website_checker

# Set DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/website_checker

# Run migrations
python -m alembic upgrade head
```

#### SQLite (Development):
```bash
# DATABASE_URL in .env (default)
DATABASE_URL=sqlite:///./jobs.db

# Run migrations
python -m alembic upgrade head
```

### Step 4: Create First API Key

```bash
export ADMIN_API_KEY=your-admin-key-from-env
python scripts/create_api_key.py --name "Production Key"

# Save the returned API key!
```

### Step 5: Run Application

#### Development:
```bash
python -m gui.main
# Access at http://localhost:8000
```

#### Production with Uvicorn:
```bash
# Single worker
uvicorn gui.main:app --host 0.0.0.0 --port 8000

# Multiple workers (recommended)
uvicorn gui.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Production with Gunicorn:
```bash
pip install gunicorn

gunicorn gui.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

---

## Production Checklist

### Security ✅
- [ ] Generated strong `SECRET_KEY`
- [ ] Generated strong `ADMIN_API_KEY`
- [ ] Set `ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Configured `ALLOWED_ORIGINS` (no wildcards!)
- [ ] Enabled `SSL_VERIFY_DEFAULT=true`
- [ ] Enabled `RATE_LIMIT_ENABLED=true`
- [ ] Configured `ENABLE_SECURITY_HEADERS=true`
- [ ] Set up SSL/TLS (HTTPS)
- [ ] Configured firewall rules
- [ ] Database password is strong
- [ ] Created backup admin API key (stored securely)

### Configuration ✅
- [ ] Set correct `ALLOWED_ORIGINS` for CORS
- [ ] Configured `DATABASE_URL` for PostgreSQL
- [ ] Set `LOG_FORMAT=json` for structured logging
- [ ] Configured `MAX_UPLOAD_SIZE_MB` appropriately
- [ ] Set `JOB_RETENTION_HOURS` for cleanup
- [ ] Adjusted `WORKERS` based on CPU cores
- [ ] Configured `MAX_CONCURRENT_JOBS`
- [ ] Set `SENTRY_DSN` for error tracking (optional)

### Infrastructure ✅
- [ ] Database backup strategy in place
- [ ] Log aggregation configured
- [ ] Monitoring/alerting set up
- [ ] Health check endpoints configured
- [ ] Reverse proxy configured (nginx, Traefik, etc.)
- [ ] SSL certificates installed
- [ ] Firewall rules applied
- [ ] Persistent volumes for uploads/exports
- [ ] Resource limits configured

### Testing ✅
- [ ] Health check responds: `curl https://your-domain.com/health`
- [ ] Database connectivity works
- [ ] API key authentication works
- [ ] File upload works
- [ ] Processing jobs work
- [ ] Rate limiting works
- [ ] Metrics endpoint accessible: `/metrics`
- [ ] Admin endpoints require auth
- [ ] Load testing completed
- [ ] Backup restoration tested

---

## Reverse Proxy Setup

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # File upload size
    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for SSE)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }

    # Static files (if serving separately)
    location /static/ {
        alias /app/gui/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Traefik Configuration (Docker Labels)

```yaml
services:
  web:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.website-checker.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.website-checker.entrypoints=websecure"
      - "traefik.http.routers.website-checker.tls.certresolver=letsencrypt"
      - "traefik.http.services.website-checker.loadbalancer.server.port=8000"
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Basic health
curl https://your-domain.com/health

# Detailed health (with system metrics)
curl https://your-domain.com/health/detailed

# Liveness (Kubernetes)
curl https://your-domain.com/health/live

# Readiness (Kubernetes)
curl https://your-domain.com/health/ready
```

### Prometheus Metrics

Access metrics at: `https://your-domain.com/metrics`

Key metrics to monitor:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `active_jobs` - Currently processing jobs
- `database_connections` - DB connection pool
- `memory_usage_bytes` - Application memory
- `cpu_percent` - CPU usage

### Log Monitoring

```bash
# Docker Compose
docker-compose logs -f web

# Docker
docker logs -f website-checker

# Manual deployment
tail -f logs/app.log

# JSON logs (recommended for aggregation)
docker-compose logs web | jq .
```

### Database Backup

```bash
# Docker Compose PostgreSQL backup
docker-compose exec db pg_dump -U checker website_checker > backup.sql

# Restore
docker-compose exec -T db psql -U checker website_checker < backup.sql

# Automated backup (add to cron)
0 2 * * * /path/to/backup-script.sh
```

### Cleanup Old Files

Files are automatically cleaned up based on `JOB_RETENTION_HOURS`.
Manual cleanup:
```bash
# Remove files older than 24 hours
find gui/uploads -type f -mtime +1 -delete
find gui/exports -type f -mtime +1 -delete
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml - add multiple web instances
services:
  web:
    deploy:
      replicas: 3
    # ... rest of config
```

### Load Balancing

Use nginx, Traefik, or cloud load balancer to distribute traffic.

**Important**: When scaling horizontally:
- Use PostgreSQL (not SQLite)
- Configure shared storage for uploads/exports
- Consider Redis for rate limiting (future enhancement)

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs web

# Common issues:
# 1. Missing SECRET_KEY or ADMIN_API_KEY
#    Solution: Set in .env file

# 2. Database connection failed
#    Solution: Check DATABASE_URL and db service status

# 3. Port already in use
#    Solution: Change PORT in .env or stop conflicting service
```

### Database Issues

```bash
# Check database status
docker-compose exec db pg_isready

# Check migrations
python -m alembic current

# Reset database (DESTRUCTIVE!)
docker-compose down -v  # Removes data!
docker-compose up -d
python -m alembic upgrade head
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check database queries
docker-compose exec db psql -U checker -c "SELECT * FROM pg_stat_activity;"

# Check application metrics
curl http://localhost:8000/health/detailed
```

### Authentication Problems

```bash
# List API keys (requires admin key)
curl "http://localhost:8000/api/admin/api-keys?admin_key=YOUR_ADMIN_KEY"

# Create new API key
python scripts/create_api_key.py --name "New Key"

# Test authentication
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/api/admin/status
```

---

## Security Best Practices

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Rotate secrets regularly** - Every 90 days recommended
3. **Use strong passwords** - 32+ character random strings
4. **Enable HTTPS** - Use Let's Encrypt or similar
5. **Limit CORS origins** - Never use wildcards in production
6. **Monitor failed auth attempts** - Check logs regularly
7. **Keep dependencies updated** - Run `pip list --outdated`
8. **Use firewall** - Only expose necessary ports
9. **Regular backups** - Automated daily backups
10. **Security scanning** - Use tools like `bandit`, `safety`

---

## Kubernetes Deployment (Advanced)

See `k8s/` directory for example manifests (to be created).

Basic deployment:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

---

## Support & Resources

- **Documentation**: `/docs` directory
- **Health Check**: `/health/detailed`
- **Metrics**: `/metrics`
- **API Docs**: `/api/docs` (disabled in production)
- **GitHub Issues**: Report bugs and feature requests

---

**Last Updated**: 2025-12-31
**Version**: 1.0.0
**Deployment Status**: Production Ready ✅
