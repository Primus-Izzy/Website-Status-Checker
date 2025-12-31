#!/bin/bash
# Database Restore Script for Website Status Checker
# Usage: ./scripts/restore.sh <backup_file>

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Backup file required"
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Example:"
    echo "  $0 ./backups/website_checker_20250131_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite the current database!"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

echo "🔄 Starting database restore..."
echo "📁 Backup file: $BACKUP_FILE"

# Check if file is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "🗜️  Decompressing backup..."
    gunzip -c "$BACKUP_FILE" > /tmp/restore.sql
    RESTORE_FILE="/tmp/restore.sql"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Check if running in Docker Compose
if docker-compose ps db &>/dev/null; then
    echo "🐳 Using Docker Compose..."

    # Drop and recreate database
    docker-compose exec -T db psql -U checker -d postgres -c "DROP DATABASE IF EXISTS website_checker;"
    docker-compose exec -T db psql -U checker -d postgres -c "CREATE DATABASE website_checker;"

    # Restore backup
    docker-compose exec -T db psql -U checker -d website_checker < "$RESTORE_FILE"
else
    echo "💻 Using local PostgreSQL..."

    # Drop and recreate database
    psql -h localhost -U checker -d postgres -c "DROP DATABASE IF EXISTS website_checker;"
    psql -h localhost -U checker -d postgres -c "CREATE DATABASE website_checker;"

    # Restore backup
    psql -h localhost -U checker -d website_checker < "$RESTORE_FILE"
fi

# Clean up temp file
if [[ "$BACKUP_FILE" == *.gz ]]; then
    rm -f /tmp/restore.sql
fi

echo "✅ Database restored successfully!"
echo "🔄 Restarting web service..."

# Restart web service if using Docker Compose
if docker-compose ps web &>/dev/null; then
    docker-compose restart web
fi

echo "✅ Restore completed!"
