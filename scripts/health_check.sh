#!/bin/bash
# Health Check Script for Website Status Checker
# Usage: ./scripts/health_check.sh [url]

URL="${1:-http://localhost:8000}"

echo "🏥 Health Check for Website Status Checker"
echo "🔗 URL: $URL"
echo ""

# Basic health check
echo "1️⃣  Basic Health Check..."
HEALTH=$(curl -s "${URL}/health" || echo "FAILED")

if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Basic health: OK"
else
    echo "❌ Basic health: FAILED"
    exit 1
fi

# Detailed health check
echo ""
echo "2️⃣  Detailed Health Check..."
DETAILED=$(curl -s "${URL}/health/detailed" || echo "FAILED")

if echo "$DETAILED" | grep -q "status"; then
    echo "✅ Detailed health: OK"
    echo ""
    echo "📊 Health Details:"
    echo "$DETAILED" | python3 -m json.tool 2>/dev/null || echo "$DETAILED"
else
    echo "❌ Detailed health: FAILED"
fi

# Liveness probe
echo ""
echo "3️⃣  Liveness Probe..."
LIVE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}/health/live")

if [ "$LIVE" = "200" ]; then
    echo "✅ Liveness: OK (HTTP $LIVE)"
else
    echo "❌ Liveness: FAILED (HTTP $LIVE)"
fi

# Readiness probe
echo ""
echo "4️⃣  Readiness Probe..."
READY=$(curl -s -o /dev/null -w "%{http_code}" "${URL}/health/ready")

if [ "$READY" = "200" ]; then
    echo "✅ Readiness: OK (HTTP $READY)"
else
    echo "❌ Readiness: FAILED (HTTP $READY)"
fi

# Check metrics endpoint
echo ""
echo "5️⃣  Metrics Endpoint..."
METRICS=$(curl -s -o /dev/null -w "%{http_code}" "${URL}/metrics")

if [ "$METRICS" = "200" ]; then
    echo "✅ Metrics: OK (HTTP $METRICS)"
else
    echo "⚠️  Metrics: Not available (HTTP $METRICS)"
fi

echo ""
echo "🎉 Health check completed!"
