[8m# Podman Deployment Guide

## Overview

The Red Team Exercise Manager is now deployed and running using Podman on macOS.

## Current Deployment Status

✅ **Container Built**: `redteam-app:latest` (~200MB)
✅ **Pod Created**: `redteam-pod`
✅ **Application Running**: Port 5172
✅ **Health Checks**: Passing (liveness & readiness)

## Access the Application

**Web Interface**: http://localhost:5172

**API Endpoints**:
- Health Check: http://localhost:5172/api/health
- Liveness: http://localhost:5172/api/liveness
- Readiness: http://localhost:5172/api/readiness

## Deployment Architecture

```
redteam-pod (Podman Pod)
├── Infrastructure container (networking)
└── redteam-app (application container)
    ├── Port: 5172:5172
    ├── Volumes:
    │   ├── ./db → /app/db (database)
    │   └── ./logs → /app/logs (logs)
    └── Environment:
        ├── ENVIRONMENT=production
        ├── LOG_LEVEL=INFO
        ├── LOG_FORMAT=json
        └── SECRET_KEY=production-secret-change-me
```

## Quick Commands

### Pod Management

```bash
# List pods
podman pod ps

# List containers in pod
podman ps --filter pod=redteam-pod

# Pod logs
podman logs redteam-app

# Follow logs
podman logs -f redteam-app

# Stop pod
podman pod stop redteam-pod

# Start pod
podman pod start redteam-pod

# Restart pod
podman pod restart redteam-pod

# Remove pod (stops all containers)
podman pod rm -f redteam-pod
```

### Container Management

```bash
# Container status
podman ps

# Container logs
podman logs redteam-app --tail 50

# Container stats
podman stats redteam-app

# Execute command in container
podman exec -it redteam-app /bin/bash

# Inspect container
podman inspect redteam-app
```

### Image Management

```bash
# List images
podman images

# Remove old images
podman image prune -a

# Rebuild image
podman build -f Containerfile -t redteam-app:latest .

# Export image
podman save -o redteam-app.tar redteam-app:latest

# Import image
podman load -i redteam-app.tar
```

## Rebuild and Redeploy

```bash
# Stop and remove existing deployment
podman stop redteam-app
podman rm redteam-app

# Rebuild image
podman build -f Containerfile -t redteam-app:latest .

# Run new container
podman run -d --pod redteam-pod \
  --name redteam-app \
  -v ./db:/app/db:Z \
  -v ./logs:/app/logs:Z \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  -e LOG_FORMAT=json \
  -e DATABASE_URL=sqlite:///./db/redteam.db \
  -e SECRET_KEY=production-secret-change-me \
  -e RATE_LIMIT_PER_MINUTE=60 \
  redteam-app:latest

# Verify
podman ps --filter pod=redteam-pod
curl http://localhost:5172/api/liveness
```

## Full Deployment from Scratch

```bash
# 1. Create pod with port mapping
podman pod create --name redteam-pod -p 5172:5172

# 2. Create required directories
mkdir -p db logs

# 3. Build image
podman build -f Containerfile -t redteam-app:latest .

# 4. Run container in pod
podman run -d --pod redteam-pod \
  --name redteam-app \
  -v ./db:/app/db:Z \
  -v ./logs:/app/logs:Z \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  -e LOG_FORMAT=json \
  -e DATABASE_URL=sqlite:///./db/redteam.db \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  -e RATE_LIMIT_PER_MINUTE=60 \
  redteam-app:latest

# 5. Verify deployment
sleep 10
curl http://localhost:5172/api/health
curl http://localhost:5172/api/liveness
curl http://localhost:5172/api/readiness
```

## Configuration

### Environment Variables

```bash
# Production settings
-e ENVIRONMENT=production
-e DEBUG=false

# Logging
-e LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
-e LOG_FORMAT=json         # json or text

# Security
-e SECRET_KEY=<random-32-char-hex>
-e RATE_LIMIT_PER_MINUTE=60

# Database (SQLite)
-e DATABASE_URL=sqlite:///./db/redteam.db

# Database (PostgreSQL)
-e DATABASE_URL=postgresql://user:pass@host:5432/redteam
```

### Volume Mounts

```bash
# Database persistence
-v ./db:/app/db:Z

# Log persistence
-v ./logs:/app/logs:Z

# Static files (optional override)
-v ./static:/app/static:Z

# Templates (optional override)
-v ./templates:/app/templates:Z
```

**Note**: The `:Z` flag is required on SELinux systems (including Podman on macOS) to relabel the volumes for container access.

## Health Monitoring

### Manual Health Checks

```bash
# API health check
curl http://localhost:5172/api/health | jq

# Liveness probe
curl http://localhost:5172/api/liveness

# Readiness probe
curl http://localhost:5172/api/readiness
```

### Automated Monitoring

```bash
# Watch pod status
watch -n 5 'podman pod ps'

# Monitor logs
podman logs -f redteam-app | grep -E "ERROR|WARNING"

# Check resource usage
podman stats redteam-app
```

## Systemd Integration (Linux)

For production deployments on Linux, use systemd for automatic startup:

```bash
# Generate systemd unit files
cd /home/ubuntu/redteam_py_app
podman generate systemd --name redteam-pod --files

# Move to systemd directory
sudo mv pod-redteam-pod.service /etc/systemd/system/
sudo mv container-redteam-app.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable pod-redteam-pod.service
sudo systemctl start pod-redteam-pod.service

# Check status
sudo systemctl status pod-redteam-pod.service
```

## Kubernetes Deployment

Convert Podman pod to Kubernetes manifest:

```bash
# Generate Kubernetes YAML
podman generate kube redteam-pod > redteam-k8s.yaml

# Deploy to Kubernetes
kubectl apply -f redteam-k8s.yaml
```

## Backup and Restore

### Database Backup

```bash
# Backup SQLite database
cp db/redteam.db db/redteam.db.backup.$(date +%Y%m%d)

# Automated daily backup
echo "0 2 * * * cp /path/to/redteam_py_app/db/redteam.db /backups/redteam.db.\$(date +\%Y\%m\%d)" | crontab -
```

### Full State Backup

```bash
# Backup everything
tar czf redteam-backup-$(date +%Y%m%d).tar.gz db/ logs/

# Restore
tar xzf redteam-backup-20250119.tar.gz
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
podman logs redteam-app

# Check events
podman events --filter container=redteam-app

# Inspect container
podman inspect redteam-app
```

### Port Already in Use

```bash
# Find process using port
lsof -i :5172

# Use different port
podman pod rm -f redteam-pod
podman pod create --name redteam-pod -p 8080:5172
# Redeploy container
```

### Volume Permission Issues

```bash
# Ensure directories exist and have correct permissions
mkdir -p db logs
chmod 755 db logs

# Verify SELinux labels (if applicable)
ls -lZ db logs

# Fix permissions
podman unshare chown -R 1000:1000 db logs
```

### Database Locked

```bash
# Stop application
podman stop redteam-app

# Remove lock file
rm -f db/redteam.db-shm db/redteam.db-wal

# Restart
podman start redteam-app
```

### Memory Issues

```bash
# Check container resource usage
podman stats redteam-app

# Limit memory
podman run -d --pod redteam-pod \
  --name redteam-app \
  --memory=512m \
  --memory-swap=1g \
  [other options...]
```

## Performance Tuning

### Worker Configuration

```bash
# Adjust workers based on CPU cores
-e WORKERS=4  # 2x CPU cores recommended
```

### Database Optimization

```bash
# For high load, use PostgreSQL instead of SQLite
podman run -d \
  --name postgres \
  --pod redteam-pod \
  -e POSTGRES_DB=redteam \
  -e POSTGRES_USER=redteam \
  -e POSTGRES_PASSWORD=secure_password \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:16-alpine

# Update app container
-e DATABASE_URL=postgresql://redteam:secure_password@${POSTGRES_HOST}/redteam
```

## Security Best Practices

1. **Change Secret Key**
```bash
-e SECRET_KEY=$(openssl rand -hex 32)
```

2. **Use Secrets Management**
```bash
# Create secret
echo "my-secret-key" | podman secret create redteam_secret -

# Use in container
podman run --secret redteam_secret ...
```

3. **Run Rootless**
```bash
# Already configured - container runs as appuser (non-root)
```

4. **Network Isolation**
```bash
# Create isolated network
podman network create redteam-net

# Use in pod
podman pod create --name redteam-pod --network redteam-net -p 5172:5172
```

## Current Deployment Info

**Container ID**: `c37659f86be7`
**Image**: `localhost/redteam-app:latest`
**Pod**: `redteam-pod` (ID: `ecb6ce5a9921`)
**Status**: ✅ Running
**Port**: `0.0.0.0:5172 → 5172`
**Volumes**:
- `./db → /app/db`
- `./logs → /app/logs`

**Environment**:
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `LOG_FORMAT=json`

## Next Steps

1. **Access the application**: http://localhost:5172
2. **Change SECRET_KEY** to a secure random value
3. **Configure backups** for the database
4. **Setup monitoring** and alerting
5. **Review logs**: `podman logs -f redteam-app`
6. **Test functionality**: Create exercises, view templates

## Additional Resources

- Podman Documentation: https://docs.podman.io/
- Project README: [README.md](README.md)
- Full Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Production Checklist: [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)
[0m