[8m# Production Deployment Checklist

## Pre-Deployment

### Code Quality
- [x] All tests passing (`make test`)
- [x] Code linted (`make lint`)
- [x] Security scan completed (`make security`)
- [x] Type checking passed (`mypy app/`)
- [ ] Code review completed
- [ ] Documentation updated

### Configuration
- [ ] `.env` file created from `.env.example`
- [ ] `SECRET_KEY` set to cryptographically random value
- [ ] `ENVIRONMENT=production` configured
- [ ] `DEBUG=false` set
- [ ] `DATABASE_URL` configured (PostgreSQL recommended)
- [ ] `ALLOWED_HOSTS` restricted to known domains
- [ ] `CORS_ORIGINS` configured if needed
- [ ] `LOG_LEVEL` set appropriately (INFO or WARNING)
- [ ] `RATE_LIMIT_PER_MINUTE` reviewed

### Security
- [ ] SSL/TLS certificate obtained and configured
- [ ] Firewall rules configured (only 80, 443, SSH)
- [ ] Secret key rotated from default
- [ ] Database credentials secured
- [ ] Non-root user configured in container
- [ ] Security headers verified (`curl -I https://your-domain.com`)
- [ ] Rate limiting tested
- [ ] CORS policy tested
- [ ] SQL injection testing completed
- [ ] XSS protection verified

### Database
- [ ] Production database provisioned
- [ ] Database backups configured
- [ ] Migrations tested in staging
- [ ] Database user has minimum required permissions
- [ ] Connection pooling configured
- [ ] Database performance tuning completed
- [ ] Backup restoration tested

### Infrastructure
- [ ] Container registry access configured
- [ ] Container image built and pushed
- [ ] Health check endpoints verified
- [ ] Resource limits set (CPU, memory)
- [ ] Persistent storage configured for database
- [ ] Log aggregation configured
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented

### Monitoring & Observability
- [ ] Health endpoint monitored (`/api/health`)
- [ ] Application logs aggregated
- [ ] Error tracking configured (Sentry, etc.)
- [ ] Performance monitoring active
- [ ] Uptime monitoring configured
- [ ] Alert thresholds defined
- [ ] On-call rotation established

### Performance
- [ ] Load testing completed
- [ ] Database queries optimized
- [ ] Static assets served via CDN
- [ ] Response caching configured
- [ ] Worker count optimized
- [ ] Connection pool tuned

### Documentation
- [x] README.md complete
- [x] DEPLOYMENT.md written
- [ ] Architecture diagram created
- [ ] API documentation generated
- [ ] Runbook for common operations
- [ ] Incident response procedures
- [ ] Rollback procedures documented

## Deployment Steps

1. **Pre-deployment verification**
```bash
# Run all checks
make check-all

# Verify deployment readiness
make deploy-check
```

2. **Build and tag container**
```bash
docker build -f Containerfile -t redteam-app:1.0.0 .
docker tag redteam-app:1.0.0 redteam-app:latest
```

3. **Push to registry**
```bash
docker push your-registry/redteam-app:1.0.0
docker push your-registry/redteam-app:latest
```

4. **Deploy to production**
```bash
# Docker Compose
docker-compose up -d

# Or Kubernetes
kubectl apply -f k8s/

# Or cloud platform
# Follow platform-specific instructions
```

5. **Verify deployment**
```bash
# Health check
curl https://your-domain.com/api/health

# Liveness
curl https://your-domain.com/api/liveness

# Readiness
curl https://your-domain.com/api/readiness

# Smoke test
curl https://your-domain.com/
```

6. **Monitor initial rollout**
- Watch logs for errors
- Monitor response times
- Check database connections
- Verify health metrics
- Test critical user flows

## Post-Deployment

### Immediate (First Hour)
- [ ] All health checks passing
- [ ] No critical errors in logs
- [ ] Response times within SLA
- [ ] Database connections stable
- [ ] Static assets loading
- [ ] Authentication working
- [ ] Key workflows tested

### First Day
- [ ] Monitor error rates
- [ ] Review performance metrics
- [ ] Check resource utilization
- [ ] Verify backup completion
- [ ] Test alerting system
- [ ] Gather user feedback

### First Week
- [ ] Analyze usage patterns
- [ ] Review security logs
- [ ] Optimize slow queries
- [ ] Adjust resource limits
- [ ] Update documentation with learnings
- [ ] Plan next iteration

## Rollback Procedure

If issues occur:

1. **Immediate rollback**
```bash
# Docker Compose
docker-compose down
docker-compose up -d --force-recreate

# Kubernetes
kubectl rollout undo deployment/redteam-app

# Tag previous version as latest
docker tag redteam-app:previous redteam-app:latest
```

2. **Database rollback** (if migrations ran)
```bash
make migrate-rollback
```

3. **Verify rollback**
```bash
curl https://your-domain.com/api/health
```

4. **Root cause analysis**
- Collect logs
- Review metrics
- Document issue
- Create fix plan

## Environment-Specific Notes

### Development
- DEBUG=true
- SQLite database
- Hot reload enabled
- Detailed error pages

### Staging
- Mirror production config
- Test data population
- Full test suite runs
- Performance testing

### Production
- DEBUG=false
- PostgreSQL/managed DB
- Multiple workers
- Error reporting only
- SSL/TLS required
- Rate limiting active

## Maintenance Windows

Recommended schedule:
- **Patches**: Weekly off-hours
- **Minor updates**: Bi-weekly during maintenance window
- **Major updates**: Quarterly with full testing
- **Database maintenance**: Monthly during low-traffic periods

## Contacts

- **Application Owner**: [Name/Email]
- **Operations Team**: [Email/Slack]
- **Security Team**: [Email]
- **On-Call**: [PagerDuty/Phone]

## Tools & Access

- **Container Registry**: [URL]
- **Monitoring Dashboard**: [URL]
- **Log Aggregation**: [URL]
- **CI/CD Pipeline**: [URL]
- **Wiki/Docs**: [URL]
[0m