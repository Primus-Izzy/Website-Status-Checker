# Architecture Documentation

Complete system architecture for Website Status Checker.

---

## System Overview

Website Status Checker is a production-grade, cloud-native application for checking website availability at scale.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Users/Clients                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTPS
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    Load Balancer / Ingress                       │
│              (nginx, Traefik, ALB, etc.)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
         ┌──────▼────┐ ┌───▼──────┐ ┌─▼────────┐
         │   Web     │ │   Web    │ │   Web    │
         │ Instance  │ │ Instance │ │ Instance │
         │    #1     │ │    #2    │ │    #3    │
         └─────┬─────┘ └────┬─────┘ └────┬─────┘
               │            │            │
               └────────────┼────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
      ┌─────▼─────┐   ┌────▼────┐   ┌─────▼──────┐
      │PostgreSQL │   │  File   │   │ Prometheus │
      │  Database │   │ Storage │   │  Metrics   │
      └───────────┘   └─────────┘   └─────┬──────┘
                                            │
                                    ┌───────▼──────┐
                                    │   Grafana    │
                                    │  Dashboards  │
                                    └──────────────┘
```

---

## Component Architecture

### Application Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web GUI    │  │   REST API   │  │   CLI Tool   │          │
│  │  (FastAPI)   │  │  (FastAPI)   │  │  (asyncio)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│  ┌──────▼─────────────────▼─────────────────▼──────┐           │
│  │           Middleware Layer                       │           │
│  │  - Authentication                                │           │
│  │  - Rate Limiting                                 │           │
│  │  - Logging                                       │           │
│  │  - Error Tracking                                │           │
│  │  - Metrics Collection                            │           │
│  └──────┬────────────────────────────────────────┬──┘           │
│         │                                        │              │
│  ┌──────▼────────┐                      ┌────────▼────────┐    │
│  │  Core Engine  │                      │  Job Manager    │    │
│  │  - URL Checker│                      │  - Queue        │    │
│  │  - Async HTTP │                      │  - Scheduler    │    │
│  │  - Validation │                      │  - Status Track │    │
│  └──────┬────────┘                      └────────┬────────┘    │
│         │                                        │              │
│  ┌──────▼────────────────────────────────────────▼──────┐      │
│  │              Database Layer (SQLAlchemy)             │      │
│  │  - Models (Jobs, URLCheckResult, APIKey)             │      │
│  │  - Session Management                                │      │
│  │  - Connection Pooling                                │      │
│  └───────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
┌──────┐
│Client│
└───┬──┘
    │ 1. HTTP Request
    │    (with API key)
    ▼
┌───────────────┐
│   Ingress     │
│ (SSL Term.)   │
└───┬───────────┘
    │ 2. Forward to Web Instance
    ▼
┌───────────────┐
│  Web Instance │
│   (FastAPI)   │
├───────────────┤
│ 3. Middleware │
│    - Auth     │
│    - Rate     │
│    - Logging  │
└───┬───────────┘
    │ 4. Route to Handler
    ▼
┌───────────────┐
│  API Handler  │
│  (Endpoint)   │
└───┬───────────┘
    │ 5. Business Logic
    ▼
┌───────────────┐
│ Core Services │
│  - Checker    │
│  - Batch      │
└───┬───────────┘
    │ 6. Database Operations
    ▼
┌───────────────┐
│  PostgreSQL   │
│   Database    │
└───┬───────────┘
    │ 7. Results
    ▼
┌───────────────┐
│  Response     │
│  (JSON/CSV)   │
└───┬───────────┘
    │ 8. Send to Client
    ▼
┌──────┐
│Client│
└──────┘
```

---

## Data Flow

### Job Processing Flow

```
┌──────────────┐
│ User uploads │
│  CSV file    │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ File Validation      │
│ - Type check         │
│ - Size check         │
│ - Content validation │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Create Job Record    │
│ - Generate ID        │
│ - Set status:pending │
│ - Store metadata     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Parse URLs from File │
│ - Extract URLs       │
│ - Validate format    │
│ - Deduplicate        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Set status:processing│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Process URLs         │
│ (async, concurrent)  │
│                      │
│  For each URL:       │
│  1. HTTP GET request │
│  2. Measure latency  │
│  3. Check status     │
│  4. Handle errors    │
│  5. Save result      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Update Progress      │
│ (via SSE)            │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Set status:completed │
│ or status:failed     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Generate Export      │
│ - CSV/JSON/Excel     │
│ - Store file         │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Cleanup (after TTL)  │
│ - Delete files       │
│ - Delete DB records  │
└──────────────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────┐
│              jobs                        │
├─────────────────────────────────────────┤
│ id              UUID PRIMARY KEY         │
│ filename        VARCHAR(255)             │
│ status          VARCHAR(20)              │
│ total_urls      INTEGER                  │
│ processed_urls  INTEGER                  │
│ active_count    INTEGER                  │
│ inactive_count  INTEGER                  │
│ error_count     INTEGER                  │
│ upload_path     VARCHAR(512)             │
│ export_path     VARCHAR(512)             │
│ created_at      TIMESTAMP                │
│ updated_at      TIMESTAMP                │
│ error_message   TEXT                     │
└──────────┬──────────────────────────────┘
           │
           │ one-to-many
           │
┌──────────▼──────────────────────────────┐
│        url_check_results                 │
├─────────────────────────────────────────┤
│ id              UUID PRIMARY KEY         │
│ job_id          UUID FOREIGN KEY         │
│ url             VARCHAR(2048)            │
│ status          VARCHAR(20)              │
│ http_status     INTEGER                  │
│ response_time   FLOAT                    │
│ error_message   TEXT                     │
│ checked_at      TIMESTAMP                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│            api_keys                      │
├─────────────────────────────────────────┤
│ id              UUID PRIMARY KEY         │
│ key_hash        VARCHAR(255) UNIQUE      │
│ name            VARCHAR(255)             │
│ owner_email     VARCHAR(255)             │
│ is_active       BOOLEAN                  │
│ rate_limit_hour INTEGER                  │
│ created_at      TIMESTAMP                │
│ last_used_at    TIMESTAMP                │
└─────────────────────────────────────────┘
```

---

## Deployment Architectures

### Docker Compose Deployment

```
┌──────────────────────────────────────────────────────────┐
│                     Docker Host                          │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────┐        │
│  │        website-checker network               │        │
│  │                                              │        │
│  │  ┌──────────────┐      ┌──────────────┐     │        │
│  │  │     web      │      │  postgres    │     │        │
│  │  │  container   │◄─────┤  container   │     │        │
│  │  │  (3 replicas)│      │              │     │        │
│  │  └──────┬───────┘      └──────┬───────┘     │        │
│  │         │                     │             │        │
│  │         │              ┌──────▼───────┐     │        │
│  │         │              │postgres_data │     │        │
│  │         │              │   volume     │     │        │
│  │         │              └──────────────┘     │        │
│  │         │                                   │        │
│  │  ┌──────▼───────┐      ┌──────────────┐     │        │
│  │  │ prometheus   │      │   grafana    │     │        │
│  │  │  container   │──────►   container  │     │        │
│  │  └──────────────┘      └──────────────┘     │        │
│  │                                              │        │
│  └─────────────────────────────────────────────┘        │
│                                                           │
│  Exposed Ports:                                          │
│  - 8000 (web)                                            │
│  - 5432 (postgres)                                       │
│  - 9090 (prometheus)                                     │
│  - 3000 (grafana)                                        │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Kubernetes Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │         website-checker namespace               │         │
│  │                                                 │         │
│  │  ┌────────────────────────────────────┐        │         │
│  │  │         Ingress                    │        │         │
│  │  │  - SSL/TLS termination             │        │         │
│  │  │  - Load balancing                  │        │         │
│  │  └───────────┬────────────────────────┘        │         │
│  │              │                                  │         │
│  │  ┌───────────▼────────────────────┐            │         │
│  │  │      Service (ClusterIP)       │            │         │
│  │  └───────────┬────────────────────┘            │         │
│  │              │                                  │         │
│  │  ┌───────────▼────────────────────┐            │         │
│  │  │   Deployment (website-checker) │            │         │
│  │  │                                 │            │         │
│  │  │  ┌──────┐  ┌──────┐  ┌──────┐  │            │         │
│  │  │  │ Pod  │  │ Pod  │  │ Pod  │  │            │         │
│  │  │  │  #1  │  │  #2  │  │  #3  │  │            │         │
│  │  │  └──┬───┘  └──┬───┘  └──┬───┘  │            │         │
│  │  │     │         │         │       │            │         │
│  │  └─────┼─────────┼─────────┼───────┘            │         │
│  │        │         │         │                    │         │
│  │  ┌─────▼─────────▼─────────▼───────┐            │         │
│  │  │  PostgreSQL StatefulSet         │            │         │
│  │  │  ┌──────────────────┐            │            │         │
│  │  │  │   postgres-0     │            │            │         │
│  │  │  └────────┬─────────┘            │            │         │
│  │  │           │                      │            │         │
│  │  │  ┌────────▼─────────┐            │            │         │
│  │  │  │  PVC (10Gi)      │            │            │         │
│  │  │  └──────────────────┘            │            │         │
│  │  └──────────────────────────────────┘            │         │
│  │                                                   │         │
│  │  ┌────────────────────────────────────┐          │         │
│  │  │  HorizontalPodAutoscaler           │          │         │
│  │  │  - Min replicas: 2                 │          │         │
│  │  │  - Max replicas: 10                │          │         │
│  │  │  - Target CPU: 70%                 │          │         │
│  │  │  - Target Memory: 80%              │          │         │
│  │  └────────────────────────────────────┘          │         │
│  │                                                   │         │
│  └───────────────────────────────────────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────┐
│             Security Layers                      │
├─────────────────────────────────────────────────┤
│                                                  │
│  Layer 1: Network Security                      │
│  ┌────────────────────────────────────┐         │
│  │ - Firewall rules                   │         │
│  │ - VPC/Network isolation            │         │
│  │ - DDoS protection                  │         │
│  └────────────────────────────────────┘         │
│                     ▼                            │
│  Layer 2: Transport Security                    │
│  ┌────────────────────────────────────┐         │
│  │ - SSL/TLS (HTTPS only)             │         │
│  │ - Certificate management           │         │
│  │ - Secure ciphers                   │         │
│  └────────────────────────────────────┘         │
│                     ▼                            │
│  Layer 3: Application Security                  │
│  ┌────────────────────────────────────┐         │
│  │ - API key authentication           │         │
│  │ - Rate limiting                    │         │
│  │ - CORS protection                  │         │
│  │ - Security headers                 │         │
│  └────────────────────────────────────┘         │
│                     ▼                            │
│  Layer 4: Input Validation                      │
│  ┌────────────────────────────────────┐         │
│  │ - File type validation             │         │
│  │ - File size limits                 │         │
│  │ - URL validation                   │         │
│  │ - SQL injection protection         │         │
│  │ - SSRF protection                  │         │
│  └────────────────────────────────────┘         │
│                     ▼                            │
│  Layer 5: Data Protection                       │
│  ┌────────────────────────────────────┐         │
│  │ - Encrypted secrets                │         │
│  │ - Database encryption              │         │
│  │ - Secure password hashing          │         │
│  └────────────────────────────────────┘         │
│                     ▼                            │
│  Layer 6: Monitoring & Audit                    │
│  ┌────────────────────────────────────┐         │
│  │ - Access logging                   │         │
│  │ - Security event tracking          │         │
│  │ - Anomaly detection                │         │
│  └────────────────────────────────────┘         │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Monitoring Stack                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────┐              │
│  │     Application Instances             │              │
│  │  - Expose /metrics endpoint           │              │
│  │  - Emit structured logs               │              │
│  │  - Send error events                  │              │
│  └────────┬──────────────┬───────┬───────┘              │
│           │              │       │                       │
│           │              │       │                       │
│  ┌────────▼──────┐  ┌───▼────┐  │                       │
│  │  Prometheus   │  │ Loki   │  │                       │
│  │  (Metrics)    │  │ (Logs) │  │                       │
│  └────────┬──────┘  └───┬────┘  │                       │
│           │             │        │                       │
│           └──────┬──────┘        │                       │
│                  │               │                       │
│           ┌──────▼───────┐       │                       │
│           │   Grafana    │       │                       │
│           │ (Dashboards) │       │                       │
│           └──────────────┘       │                       │
│                                  │                       │
│                          ┌───────▼──────┐               │
│                          │    Sentry    │               │
│                          │   (Errors)   │               │
│                          └──────────────┘               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.8+
- **Async**: aiohttp, asyncio
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic

### Database
- **Production**: PostgreSQL 15+
- **Development**: SQLite 3
- **Connection Pooling**: SQLAlchemy pool

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose, Kubernetes
- **Reverse Proxy**: nginx, Traefik
- **Load Balancing**: Built-in (K8s Service)

### Monitoring
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logging**: Structured JSON logs
- **Error Tracking**: Sentry (optional)

### CI/CD
- **Platform**: GitHub Actions
- **Testing**: pytest, coverage
- **Security**: Bandit, Safety, Trivy
- **Code Quality**: Black, isort, flake8, mypy

---

## Scalability Design

### Horizontal Scaling

```
Single Instance → Multiple Instances → Auto-scaling

┌────────┐      ┌────────┐ ┌────────┐      ┌────────┐ ┌────────┐ ... ┌────────┐
│  Web   │  →   │  Web   │ │  Web   │  →   │  Web   │ │  Web   │     │  Web   │
│Instance│      │   #1   │ │   #2   │      │   #1   │ │   #2   │     │  #N    │
└────────┘      └────────┘ └────────┘      └────────┘ └────────┘     └────────┘
                      ↓                            ↓
              Load Balancer              HPA (Auto-scaling)
```

### Capacity Planning

| Metric | Single Instance | 3 Instances | 10 Instances |
|--------|----------------|-------------|--------------|
| **Requests/sec** | 100 | 300 | 1,000 |
| **Concurrent Jobs** | 10 | 30 | 100 |
| **Memory** | 2GB | 6GB | 20GB |
| **CPU** | 2 cores | 6 cores | 20 cores |

---

## Performance Optimization

### Caching Strategy (Future Enhancement)

```
┌────────┐     ┌────────┐     ┌──────────┐
│ Client │────►│ Redis  │────►│ Database │
└────────┘     │ Cache  │     └──────────┘
               └────────┘
                   │
              Cache Hit: Fast
              Cache Miss: Query DB
```

### Connection Pooling

```
Application
    │
    ├─► Connection Pool (20 connections)
    │       ├─► Active: 5
    │       └─► Idle: 15
    │
    └─► PostgreSQL Database
```

---

## Disaster Recovery

### Backup Strategy

```
┌────────────┐
│ Production │
│  Database  │
└──────┬─────┘
       │
       │ Daily Backup (02:00 UTC)
       ▼
┌──────────────┐
│ Local Backup │
│   Storage    │
└──────┬───────┘
       │
       │ Sync to Cloud
       ▼
┌──────────────┐     ┌──────────────┐
│   S3/GCS     │────►│  Off-site    │
│   Backup     │     │   Backup     │
└──────────────┘     └──────────────┘
```

---

**Last Updated**: 2025-12-31
**Version**: 1.1.0
**Maintainer**: Engineering Team
