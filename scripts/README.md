# Scripts Directory

Helper scripts for operating and maintaining the Website Status Checker.

## Available Scripts

### 1. API Key Management

#### `create_api_key.py`
Create and manage API keys for authentication.

**Usage:**
```bash
# Docker Compose
docker-compose exec web python scripts/create_api_key.py --name "My Key"

# Manual
python scripts/create_api_key.py --name "Production Key" --owner-email admin@example.com
```

**Options:**
- `--name` - Name/description for the API key (required)
- `--owner-email` - Owner's email address (optional)
- `--rate-limit-hour` - Hourly rate limit (default: 1000)

### 2. Database Backup

#### `backup.sh` (Linux/Mac) or `backup.bat` (Windows)
Create a backup of the PostgreSQL database.

**Usage:**
```bash
# Linux/Mac
./scripts/backup.sh [backup_directory]

# Windows
scripts\backup.bat [backup_directory]

# Default backup directory is ./backups
./scripts/backup.sh
```

**Features:**
- Automatic compression (Linux/Mac)
- Timestamped backup files
- Keeps last 7 days of backups (Linux/Mac)

### 3. Database Restore

#### `restore.sh` (Linux/Mac)
Restore database from a backup file.

**Usage:**
```bash
./scripts/restore.sh <backup_file>

# Example
./scripts/restore.sh ./backups/website_checker_20250131_120000.sql.gz
```

**Warning:** This will overwrite the current database!

### 4. Health Check

#### `health_check.sh` (Linux/Mac) or `health_check.bat` (Windows)
Comprehensive health check for the application.

**Usage:**
```bash
# Linux/Mac
./scripts/health_check.sh [url]

# Windows
scripts\health_check.bat [url]

# Default URL is http://localhost:8000
./scripts/health_check.sh
```

**Checks:**
- Basic health endpoint
- Detailed health with metrics
- Liveness probe (Kubernetes)
- Readiness probe (Kubernetes)
- Metrics endpoint availability

### 5. Cleanup

#### `cleanup.sh` (Linux/Mac)
Remove old files and database records.

**Usage:**
```bash
./scripts/cleanup.sh [hours]

# Default is 24 hours
./scripts/cleanup.sh

# Clean files older than 48 hours
./scripts/cleanup.sh 48
```

**Cleans:**
- Old uploaded files
- Old exported files
- Old job records from database

### 6. Quick Start Scripts

#### `start_gui.sh` (Linux/Mac) or `start_gui.bat` (Windows)
Quick start script for the web GUI.

**Usage:**
```bash
# Linux/Mac
./scripts/start_gui.sh

# Windows
scripts\start_gui.bat
```

## Making Scripts Executable (Linux/Mac)

```bash
chmod +x scripts/*.sh
```

## Automation with Cron (Linux/Mac)

### Daily Backup at 2 AM
```bash
0 2 * * * /path/to/website-status-checker/scripts/backup.sh
```

### Cleanup Every 6 Hours
```bash
0 */6 * * * /path/to/website-status-checker/scripts/cleanup.sh 24
```

### Health Check Every 5 Minutes
```bash
*/5 * * * * /path/to/website-status-checker/scripts/health_check.sh >> /var/log/health-check.log 2>&1
```

## Windows Task Scheduler

### Daily Backup
1. Open Task Scheduler
2. Create Task
3. Trigger: Daily at 2:00 AM
4. Action: Run `C:\path\to\scripts\backup.bat`

### Health Check Every 5 Minutes
1. Create Task
2. Trigger: Daily, repeat every 5 minutes
3. Action: Run `C:\path\to\scripts\health_check.bat`

## Docker Compose Integration

All scripts work seamlessly with Docker Compose deployments. They automatically detect if services are running in Docker and adjust accordingly.

## Requirements

### Linux/Mac
- bash
- curl
- postgresql-client (for manual deployments)
- docker & docker-compose (for containerized deployments)
- gzip (for backup compression)

### Windows
- curl (included in Windows 10+)
- docker & docker-compose (for containerized deployments)

## Troubleshooting

### Script Permission Denied (Linux/Mac)
```bash
chmod +x scripts/*.sh
```

### PostgreSQL Connection Error
- Ensure database is running: `docker-compose ps db`
- Check connection settings in `.env`
- Verify credentials

### Backup File Not Found
- Check backup directory exists
- Verify file path is correct
- Ensure backup completed successfully

## Best Practices

1. **Automated Backups**: Schedule daily backups using cron/Task Scheduler
2. **Test Restores**: Regularly test backup restoration
3. **Monitor Health**: Set up automated health checks
4. **Regular Cleanup**: Run cleanup script to prevent disk space issues
5. **Secure Scripts**: Keep scripts in version control, but never commit sensitive data

## Contributing

When adding new scripts:
1. Create both `.sh` (Linux/Mac) and `.bat` (Windows) versions
2. Update this README
3. Add usage examples
4. Include error handling
5. Test in Docker Compose and manual deployments
