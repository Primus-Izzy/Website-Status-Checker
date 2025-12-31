#!/bin/bash
# Cleanup Script for Website Status Checker
# Removes old jobs, uploads, and exports
# Usage: ./scripts/cleanup.sh [hours]

HOURS="${1:-24}"

echo "🧹 Cleanup Script for Website Status Checker"
echo "⏰ Removing files older than $HOURS hours"
echo ""

# Cleanup uploads
if [ -d "gui/uploads" ]; then
    echo "📁 Cleaning uploads directory..."
    UPLOAD_COUNT=$(find gui/uploads -type f -mmin +$((HOURS * 60)) 2>/dev/null | wc -l)
    if [ "$UPLOAD_COUNT" -gt 0 ]; then
        find gui/uploads -type f -mmin +$((HOURS * 60)) -delete 2>/dev/null
        echo "✅ Removed $UPLOAD_COUNT upload file(s)"
    else
        echo "ℹ️  No old upload files to remove"
    fi
fi

# Cleanup exports
if [ -d "gui/exports" ]; then
    echo ""
    echo "📁 Cleaning exports directory..."
    EXPORT_COUNT=$(find gui/exports -type f -mmin +$((HOURS * 60)) 2>/dev/null | wc -l)
    if [ "$EXPORT_COUNT" -gt 0 ]; then
        find gui/exports -type f -mmin +$((HOURS * 60)) -delete 2>/dev/null
        echo "✅ Removed $EXPORT_COUNT export file(s)"
    else
        echo "ℹ️  No old export files to remove"
    fi
fi

# Cleanup old jobs from database
echo ""
echo "🗄️  Cleaning old jobs from database..."

if docker-compose ps db &>/dev/null; then
    echo "🐳 Using Docker Compose..."

    # Get count before cleanup
    BEFORE=$(docker-compose exec -T db psql -U checker -d website_checker -t -c "SELECT COUNT(*) FROM jobs WHERE created_at < NOW() - INTERVAL '${HOURS} hours';" 2>/dev/null | tr -d ' ')

    if [ -n "$BEFORE" ] && [ "$BEFORE" -gt 0 ]; then
        # Delete old jobs
        docker-compose exec -T db psql -U checker -d website_checker -c "DELETE FROM jobs WHERE created_at < NOW() - INTERVAL '${HOURS} hours';" &>/dev/null
        echo "✅ Removed $BEFORE old job(s) from database"
    else
        echo "ℹ️  No old jobs to remove from database"
    fi
else
    echo "⚠️  Database not accessible via Docker Compose"
    echo "   Run this script with Docker Compose running, or manually clean the database"
fi

# Show disk space saved
echo ""
echo "💾 Disk usage:"
du -sh gui/uploads gui/exports 2>/dev/null || echo "Directories not found"

echo ""
echo "✅ Cleanup completed!"
