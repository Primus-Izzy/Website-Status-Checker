# Docker Quick Start Guide

## 🚀 Fast Deploy (5 minutes)

```bash
# 1. Generate environment file
cp .env.production.example .env

# 2. Generate secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('ADMIN_API_KEY=' + secrets.token_hex(32))" >> .env
python -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(16))" >> .env

# 3. Set your domain (edit .env)
nano .env  # Change ALLOWED_ORIGINS=https://yourdomain.com

# 4. Start services
docker-compose up -d

# 5. Check status
docker-compose ps
docker-compose logs -f web

# 6. Create API key
docker-compose exec web python scripts/create_api_key.py --name "Initial Key"

# Done! Access at http://localhost:8000
```

---

## 📋 Services

**Web Application**: http://localhost:8000
- Main API and web interface
- Health check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

**PostgreSQL Database**: localhost:5432
- Database: `website_checker`
- User: `checker`
- Password: Set in `.env`

**Prometheus** (optional): http://localhost:9090
```bash
docker-compose --profile monitoring up -d
```

**Grafana** (optional): http://localhost:3000
```bash
docker-compose --profile monitoring up -d
# Default login: admin / (set in .env)
```

---

## 🛠️ Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f web
docker-compose logs -f db

# Restart web service
docker-compose restart web

# Run migrations
docker-compose exec web python -m alembic upgrade head

# Create API key
docker-compose exec web python scripts/create_api_key.py --name "My Key"

# Access database
docker-compose exec db psql -U checker -d website_checker

# Check health
curl http://localhost:8000/health/detailed

# Backup database
docker-compose exec db pg_dump -U checker website_checker > backup.sql

# Restore database
docker-compose exec -T db psql -U checker website_checker < backup.sql
```

---

## 🔧 Configuration

Edit `.env` file to configure:
- `SECRET_KEY` - Application secret (required)
- `ADMIN_API_KEY` - Admin authentication (required)
- `DB_PASSWORD` - Database password (required)
- `ALLOWED_ORIGINS` - CORS origins (required for production)
- `WORKERS` - Number of worker processes (default: 4)
- `MAX_UPLOAD_SIZE_MB` - Max file size (default: 100)
- `LOG_LEVEL` - Logging level (default: INFO)

---

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Detailed Health (includes metrics)
```bash
curl http://localhost:8000/health/detailed | jq .
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

---

## 🔐 Security

### Generate Secure Keys
```bash
# Secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Admin API key
python -c "import secrets; print(secrets.token_hex(32))"

# Database password
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### Create API Key
```bash
docker-compose exec web python scripts/create_api_key.py \
  --name "Production Key" \
  --owner-email admin@example.com \
  --rate-limit-hour 10000
```

### List API Keys
```bash
curl "http://localhost:8000/api/admin/api-keys?admin_key=YOUR_ADMIN_KEY" | jq .
```

---

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Check .env file
cat .env | grep -E "SECRET_KEY|ADMIN_API_KEY|DB_PASSWORD"

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### Database connection failed
```bash
# Check database status
docker-compose exec db pg_isready

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Can't access web interface
```bash
# Check if web service is running
docker-compose ps web

# Check web logs
docker-compose logs web

# Test locally
docker-compose exec web curl http://localhost:8000/health
```

---

## 🔄 Updates & Maintenance

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

### Backup Data
```bash
# Backup database
docker-compose exec db pg_dump -U checker website_checker > backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v website-status-checker_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz /data
```

### Clean Up
```bash
# Remove old images
docker image prune -a

# Remove old containers
docker container prune

# Remove old volumes (CAREFUL!)
docker volume prune
```

---

## 📦 Production Deployment

### With SSL (using Traefik)
Add to `docker-compose.yml`:
```yaml
services:
  web:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.website-checker.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.website-checker.tls.certresolver=letsencrypt"
```

### With nginx reverse proxy
See `docs/DEPLOYMENT.md` for nginx configuration.

---

## 📚 More Information

- Full deployment guide: `docs/DEPLOYMENT.md`
- Production checklist: `PRODUCTION_READINESS_REPORT.md`
- API documentation: http://localhost:8000/api/docs (dev only)

---

**Questions?** Check `docs/DEPLOYMENT.md` or open an issue on GitHub.
