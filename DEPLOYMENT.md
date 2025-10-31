# Deployment Guide

## Production Deployment Options

### Option 1: Docker Compose (Recommended for Single Server)

**Requirements:**
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

**Steps:**

1. **Prepare environment**
```bash
# Clone repository
git clone <repository>
cd redteam_py_app

# Copy environment template
cp .env.example .env

# Edit configuration
vim .env
```

2. **Configure production settings**
```bash
# Required changes in .env:
SECRET_KEY=<generate-strong-secret-key>
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./db/redteam.db  # or PostgreSQL

# Optional optimizations:
WORKERS=4
RATE_LIMIT_PER_MINUTE=100
```

3. **Deploy**
```bash
# Build and start
docker-compose up -d

# Verify health
curl http://localhost:5172/api/health

# Check logs
docker-compose logs -f app
```

4. **Setup reverse proxy (nginx)**
```nginx
server {
    listen 80;
    server_name redteam.example.com;

    location / {
        proxy_pass http://localhost:5172;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 2: Kubernetes

**Requirements:**
- Kubernetes 1.24+
- kubectl configured
- Persistent storage (for database)

**Steps:**

1. **Create namespace**
```bash
kubectl create namespace redteam
```

2. **Create secrets**
```bash
kubectl create secret generic redteam-secrets \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --namespace=redteam
```

3. **Deploy application**
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redteam-app
  namespace: redteam
spec:
  replicas: 3
  selector:
    matchLabels:
      app: redteam
  template:
    metadata:
      labels:
        app: redteam
    spec:
      containers:
      - name: app
        image: ghcr.io/username/redteam-app:latest
        ports:
        - containerPort: 5172
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: redteam-secrets
              key: secret-key
        - name: DATABASE_URL
          value: "postgresql://redteam:password@postgres:5432/redteam"
        livenessProbe:
          httpGet:
            path: /api/liveness
            port: 5172
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/readiness
            port: 5172
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: data
          mountPath: /app/db
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: redteam-data

---
apiVersion: v1
kind: Service
metadata:
  name: redteam-service
  namespace: redteam
spec:
  selector:
    app: redteam
  ports:
  - port: 80
    targetPort: 5172
  type: LoadBalancer

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redteam-data
  namespace: redteam
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

Apply:
```bash
kubectl apply -f deployment.yaml
```

### Option 3: Cloud Platform (AWS/GCP/Azure)

#### AWS ECS Fargate

1. **Build and push image**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -f Containerfile -t redteam-app .
docker tag redteam-app:latest <account>.dkr.ecr.us-east-1.amazonaws.com/redteam-app:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/redteam-app:latest
```

2. **Create ECS task definition**
```json
{
  "family": "redteam-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "<account>.dkr.ecr.us-east-1.amazonaws.com/redteam-app:latest",
      "portMappings": [
        {
          "containerPort": 5172,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "DATABASE_URL", "value": "postgresql://..."}
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:redteam-secret"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5172/api/liveness || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

3. **Create ECS service**
```bash
aws ecs create-service \
  --cluster redteam-cluster \
  --service-name redteam-service \
  --task-definition redteam-app \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## Database Setup

### SQLite (Development/Small Scale)
Already configured. Data persists in `./db/redteam.db`.

### PostgreSQL (Recommended for Production)

1. **Setup PostgreSQL**
```bash
# Docker
docker run -d \
  --name redteam-postgres \
  -e POSTGRES_DB=redteam \
  -e POSTGRES_USER=redteam \
  -e POSTGRES_PASSWORD=secure_password \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16-alpine

# Or managed service (AWS RDS, GCP Cloud SQL, etc.)
```

2. **Update configuration**
```bash
DATABASE_URL=postgresql://redteam:secure_password@postgres:5432/redteam
```

3. **Run migrations**
```bash
make migrate
```

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d redteam.example.com

# Nginx config
server {
    listen 443 ssl http2;
    server_name redteam.example.com;

    ssl_certificate /etc/letsencrypt/live/redteam.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/redteam.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5172;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring Setup

### Prometheus + Grafana

1. **Add prometheus metrics endpoint**
```python
# Install: pip install prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

2. **Prometheus config**
```yaml
scrape_configs:
  - job_name: 'redteam-app'
    static_configs:
      - targets: ['redteam-app:5172']
```

### Logging (ELK Stack)

```yaml
# docker-compose.yml addition
  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    volumes:
      - ./logs:/usr/share/filebeat/logs:ro
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
    depends_on:
      - app
```

## Backup Strategy

### Database Backups

```bash
# SQLite
cp db/redteam.db db/redteam.db.backup.$(date +%Y%m%d)

# PostgreSQL
pg_dump -h localhost -U redteam redteam > backup_$(date +%Y%m%d).sql

# Automated daily backup
cat > /etc/cron.daily/redteam-backup <<'EOF'
#!/bin/bash
docker exec redteam-postgres pg_dump -U redteam redteam | gzip > /backups/redteam_$(date +\%Y\%m\%d).sql.gz
find /backups -name "redteam_*.sql.gz" -mtime +30 -delete
EOF
chmod +x /etc/cron.daily/redteam-backup
```

## Performance Tuning

### Database Connection Pooling

```python
# app/database.py
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Gunicorn Configuration

```bash
# Use Gunicorn instead of uvicorn for production
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:5172 \
  --access-logfile - \
  --error-logfile -
```

### Redis Caching

```python
# Add to docker-compose.yml
redis:
  image: redis:7-alpine
  volumes:
    - redis_data:/data

# Implement caching
from redis import Redis
cache = Redis(host='redis', port=6379)
```

## Security Hardening

1. **Generate strong secret key**
```bash
openssl rand -hex 32
```

2. **Restrict network access**
```bash
# Firewall rules (UFW example)
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

3. **Set resource limits**
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

4. **Enable audit logging**
```python
# Add to middleware
logger.info(f"User action: {action}", extra={
    "user": user_id,
    "ip": client_ip,
    "resource": resource
})
```

## Rollback Procedure

1. **Application rollback**
```bash
# Docker
docker-compose down
docker-compose up -d --scale app=3 --no-recreate

# Kubernetes
kubectl rollout undo deployment/redteam-app -n redteam
```

2. **Database rollback**
```bash
# Revert last migration
make migrate-rollback

# Or restore from backup
psql -h localhost -U redteam redteam < backup_20250119.sql
```

## Troubleshooting

### Check application health
```bash
curl -v http://localhost:5172/api/health
```

### View logs
```bash
# Docker
docker-compose logs -f app

# Kubernetes
kubectl logs -f deployment/redteam-app -n redteam

# Systemd
journalctl -u redteam-app -f
```

### Database connectivity
```bash
# Test connection
psql -h localhost -U redteam redteam -c "SELECT 1"
```

### Performance issues
```bash
# Check resource usage
docker stats redteam-app

# Database query performance
EXPLAIN ANALYZE SELECT * FROM exercises;
```
