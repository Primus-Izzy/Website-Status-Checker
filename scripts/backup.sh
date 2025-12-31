#!/bin/bash
# Database Backup Script for Website Status Checker
# Usage: ./scripts/backup.sh [backup_directory]

set -e

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/website_checker_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting database backup..."
echo "📁 Backup location: $BACKUP_FILE"

# Check if running in Docker Compose
if docker-compose ps db &>/dev/null; then
    echo "🐳 Using Docker Compose..."
    docker-compose exec -T db pg_dump -U checker website_checker > "$BACKUP_FILE"
else
    echo "💻 Using local PostgreSQL..."
    # Adjust connection parameters as needed
    pg_dump -h localhost -U checker website_checker > "$BACKUP_FILE"
fi

# Compress the backup
echo "🗜️  Compressing backup..."
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Get file size
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "✅ Backup completed successfully!"
echo "📦 File: $BACKUP_FILE"
echo "📊 Size: $SIZE"

# Optional: Keep only last 7 days of backups
find "$BACKUP_DIR" -name "website_checker_*.sql.gz" -mtime +7 -delete

echo "🧹 Old backups cleaned up (kept last 7 days)"
