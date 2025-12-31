# Kubernetes Deployment

Production-ready Kubernetes manifests for deploying Website Status Checker to any Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- nginx-ingress controller (or alternative)
- cert-manager (for SSL certificates)
- Storage provisioner (for PersistentVolumes)

## Quick Deploy

### 1. Generate Secrets

```bash
# Generate secure secrets
python -c "import secrets; print('SECRET_KEY:', secrets.token_urlsafe(32))"
python -c "import secrets; print('ADMIN_API_KEY:', secrets.token_hex(32))"
python -c "import secrets; print('DB_PASSWORD:', secrets.token_urlsafe(16))"

# Update k8s/secrets.yaml with generated values
```

### 2. Update Configuration

Edit the following files:
- `secrets.yaml` - Add generated secrets
- `ingress.yaml` - Update domain name
- `app-deployment.yaml` - Update Docker image URL

### 3. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets and config
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# Deploy database
kubectl apply -f k8s/postgres-deployment.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n website-checker --timeout=300s

# Deploy application
kubectl apply -f k8s/app-deployment.yaml

# Wait for application to be ready
kubectl wait --for=condition=ready pod -l app=website-checker -n website-checker --timeout=300s

# Run database migrations
kubectl exec -it -n website-checker deployment/website-checker -- python -m alembic upgrade head

# Create ingress
kubectl apply -f k8s/ingress.yaml

# Enable autoscaling (optional)
kubectl apply -f k8s/hpa.yaml
```

### 4. Create Initial API Key

```bash
kubectl exec -it -n website-checker deployment/website-checker -- \
  python scripts/create_api_key.py --name "Production Key"
```

### 5. Verify Deployment

```bash
# Check all pods
kubectl get pods -n website-checker

# Check services
kubectl get svc -n website-checker

# Check ingress
kubectl get ingress -n website-checker

# Test health endpoint
kubectl port-forward -n website-checker svc/website-checker 8000:8000
curl http://localhost:8000/health/detailed
```

## Manifest Files

### Core Deployment

- **namespace.yaml** - Creates the website-checker namespace
- **configmap.yaml** - Application configuration
- **secrets.yaml** - Sensitive credentials (SECRET_KEY, passwords)
- **postgres-deployment.yaml** - PostgreSQL database with persistent storage
- **app-deployment.yaml** - Main application deployment with 3 replicas
- **ingress.yaml** - HTTPS ingress with SSL termination
- **hpa.yaml** - Horizontal Pod Autoscaler (2-10 pods)

### Resource Requests/Limits

**Application Pods:**
- Requests: 500m CPU, 1Gi memory
- Limits: 2000m CPU, 4Gi memory

**PostgreSQL:**
- Requests: 250m CPU, 512Mi memory
- Limits: 1000m CPU, 2Gi memory

### Storage

**PersistentVolumeClaims:**
- `postgres-pvc`: 10Gi for database
- `uploads-pvc`: 5Gi for uploaded files (ReadWriteMany)
- `exports-pvc`: 5Gi for exported files (ReadWriteMany)

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment website-checker -n website-checker --replicas=5

# Check scaling status
kubectl get hpa -n website-checker
```

### Autoscaling

HPA automatically scales based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Min replicas: 2
- Max replicas: 10

## Monitoring

### Prometheus Integration

Pods are annotated for Prometheus scraping:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

Install Prometheus with:
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### Grafana Dashboards

Access Grafana:
```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

Import dashboard from `monitoring/grafana-dashboards/website-checker-dashboard.json`

## SSL/TLS Configuration

### Using cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

Certificates will be automatically provisioned by cert-manager.

## Database Management

### Backup

```bash
# Create backup
kubectl exec -n website-checker deployment/postgres -- \
  pg_dump -U checker website_checker > backup.sql

# Backup to PVC
kubectl exec -n website-checker deployment/postgres -- \
  pg_dump -U checker website_checker | gzip > /tmp/backup.sql.gz
```

### Restore

```bash
# Restore from backup
kubectl exec -i -n website-checker deployment/postgres -- \
  psql -U checker -d website_checker < backup.sql
```

### Migrations

```bash
# Check current migration
kubectl exec -n website-checker deployment/website-checker -- \
  python -m alembic current

# Upgrade to latest
kubectl exec -n website-checker deployment/website-checker -- \
  python -m alembic upgrade head

# Downgrade one version
kubectl exec -n website-checker deployment/website-checker -- \
  python -m alembic downgrade -1
```

## Maintenance

### Rolling Updates

```bash
# Update image
kubectl set image deployment/website-checker -n website-checker \
  web=ghcr.io/your-org/website-status-checker:v1.2.0

# Check rollout status
kubectl rollout status deployment/website-checker -n website-checker

# Rollback if needed
kubectl rollout undo deployment/website-checker -n website-checker
```

### View Logs

```bash
# Application logs
kubectl logs -n website-checker -l app=website-checker --tail=100 -f

# Database logs
kubectl logs -n website-checker -l app=postgres --tail=100 -f

# Logs from specific pod
kubectl logs -n website-checker <pod-name> -f
```

### Execute Commands

```bash
# Open shell in application pod
kubectl exec -it -n website-checker deployment/website-checker -- /bin/bash

# Run health check
kubectl exec -n website-checker deployment/website-checker -- \
  curl http://localhost:8000/health/detailed

# Create API key
kubectl exec -n website-checker deployment/website-checker -- \
  python scripts/create_api_key.py --name "New Key"
```

## Cleanup

```bash
# Delete everything
kubectl delete namespace website-checker

# Or delete individually
kubectl delete -f k8s/hpa.yaml
kubectl delete -f k8s/ingress.yaml
kubectl delete -f k8s/app-deployment.yaml
kubectl delete -f k8s/postgres-deployment.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/secrets.yaml
kubectl delete -f k8s/namespace.yaml
```

## Cloud Provider Specific Notes

### AWS EKS

```bash
# Use EBS for storage
# Add to PVC spec:
# storageClassName: gp3

# Use ALB ingress instead of nginx
# Update ingress annotations for AWS ALB Ingress Controller
```

### Google GKE

```bash
# Use GCE PD for storage
# Add to PVC spec:
# storageClassName: standard-rwo

# GKE auto-provisions load balancer
```

### Azure AKS

```bash
# Use Azure Disk for storage
# Add to PVC spec:
# storageClassName: managed-premium

# Use Azure Application Gateway ingress
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod
kubectl describe pod -n website-checker <pod-name>

# Check events
kubectl get events -n website-checker --sort-by='.lastTimestamp'

# Check logs
kubectl logs -n website-checker <pod-name>
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl exec -n website-checker deployment/website-checker -- \
  python -c "from gui.database.session import engine; engine.connect()"

# Check database pod
kubectl exec -n website-checker deployment/postgres -- pg_isready
```

### Ingress Not Working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress resource
kubectl describe ingress -n website-checker website-checker-ingress

# Check certificate
kubectl get certificate -n website-checker
```

## Security Best Practices

1. **Secrets Management**
   - Use external secret managers (AWS Secrets Manager, Vault, etc.)
   - Rotate secrets regularly
   - Never commit secrets to Git

2. **Network Policies**
   - Implement NetworkPolicies to restrict pod-to-pod communication
   - Only allow necessary ingress/egress

3. **RBAC**
   - Create ServiceAccount with minimal permissions
   - Use RBAC to control access

4. **Pod Security**
   - Run as non-root user
   - Use security contexts
   - Enable Pod Security Standards

## Performance Tuning

### Database

```yaml
# Add to postgres container env
- name: POSTGRES_SHARED_BUFFERS
  value: "256MB"
- name: POSTGRES_WORK_MEM
  value: "16MB"
- name: POSTGRES_MAX_CONNECTIONS
  value: "100"
```

### Application

```yaml
# Adjust workers based on CPU
- name: WORKERS
  value: "8"  # 2x number of CPU cores
```

## Further Reading

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [nginx-ingress Documentation](https://kubernetes.github.io/ingress-nginx/)
