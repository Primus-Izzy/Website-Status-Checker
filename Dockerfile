# Website Status Checker - Production Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-gui.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt -r requirements-gui.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    ENV=production \
    DEBUG=false

# Create app user for security (non-root)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/gui/uploads /app/gui/exports && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=appuser:appuser /root/.local /root/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Create necessary directories
RUN mkdir -p gui/uploads gui/exports logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live').read()" || exit 1

# Run database migrations on startup, then start server
CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn gui.main:app --host 0.0.0.0 --port 8000 --workers 4"]
