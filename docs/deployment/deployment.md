# Congressional Transparency Platform - Production Deployment Guide

This guide provides comprehensive instructions for deploying the Congressional Transparency Platform to production using Docker and the Traefik reverse proxy pattern.

## Overview

The production deployment includes:

- **Frontend**: React application served via nginx with optimized builds
- **Backend**: FastAPI service with production settings
- **Database**: PostgreSQL 15 with optimized configuration
- **Cache**: Redis with persistence and security
- **Monitoring**: Prometheus and Grafana for metrics and dashboards
- **Logging**: Filebeat for log aggregation
- **Backup**: Automated backup and restore procedures
- **CI/CD**: GitHub Actions for automated deployment pipeline

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Traefik       │    │    Frontend      │    │    Backend      │
│  (Reverse       │────│   (React +       │────│   (FastAPI)     │
│   Proxy)        │    │    nginx)        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────────────────────┐
                    │       Data Layer            │
                    │  ┌─────────┐ ┌───────────┐  │
                    │  │PostgreSQL│ │   Redis   │  │
                    │  │    DB   │ │  Cache    │  │
                    │  └─────────┘ └───────────┘  │
                    └─────────────────────────────┘
```

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 100GB+ SSD
- **Network**: Static IP with domain access

### Software Dependencies

- Docker 24.0+
- Docker Compose 2.20+
- Git
- curl
- AWS CLI (for S3 backups)

### Domain Requirements

The following DNS records should point to your server:

- `congress.local.team-skynet.io` - Frontend application
- `congress-api.local.team-skynet.io` - Backend API
- `congress-dashboard.local.team-skynet.io` - Grafana dashboard
- `congress-metrics.local.team-skynet.io` - Prometheus metrics

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/senate-gov.git
cd senate-gov
```

### 2. Set Up Environment

```bash
# Copy production environment template
cp .env.production .env.production.local

# Edit with your production values
nano .env.production.local
```

**Critical environment variables to update:**

```bash
# Security - Generate secure random values
SECRET_KEY=your-256-bit-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
POSTGRES_PASSWORD=your-secure-db-password
REDIS_PASSWORD=your-secure-redis-password
GRAFANA_ADMIN_PASSWORD=your-grafana-password

# API Keys
DATA_GOV_API_KEY=your-api-key-from-data-gov
SENATE_GOV_USERNAME=your-senate-username
SENATE_GOV_PASSWORD=your-senate-password

# Backup Configuration
BACKUP_S3_BUCKET=your-s3-bucket-name
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
SLACK_WEBHOOK_URL=your-slack-webhook
```

### 3. Set Up Traefik Network

```bash
# Create the backend network for Traefik integration
docker network create backend
```

### 4. Create Data Directories

```bash
# Create required directories with proper permissions
sudo mkdir -p /opt/congress-platform/{data/{postgres,redis,prometheus,grafana},backups,logs}
sudo chown -R $USER:$USER /opt/congress-platform
```

## Deployment Methods

### Option 1: Automated Deployment (Recommended)

```bash
# Make deployment script executable
chmod +x scripts/deploy-production.sh

# Deploy the full stack
./scripts/deploy-production.sh deploy
```

The script will:
1. Check prerequisites
2. Validate environment configuration
3. Create required directories
4. Build and pull Docker images
5. Run database migrations
6. Start all services
7. Run health checks
8. Display deployment status

### Option 2: Manual Deployment

```bash
# Build custom images
docker build -f Dockerfile.frontend --target production -t congress-frontend:latest .
docker build -f Dockerfile.backend --target production -t congress-backend:latest .

# Start the full stack
docker-compose -f docker-compose.prod.yml --env-file .env.production.local up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps
```

## Service URLs

After successful deployment, access the platform at:

- **Frontend**: https://congress.local.team-skynet.io
- **API Documentation**: https://congress-api.local.team-skynet.io/docs
- **Grafana Dashboard**: https://congress-dashboard.local.team-skynet.io
- **Prometheus Metrics**: https://congress-metrics.local.team-skynet.io

## Monitoring and Observability

### Grafana Dashboards

Access Grafana at https://congress-dashboard.local.team-skynet.io

Default login:
- Username: `admin`
- Password: Value from `GRAFANA_ADMIN_PASSWORD`

Pre-configured dashboards include:
- Congressional Platform Overview
- API Performance Metrics
- Database Performance
- System Resource Usage

### Prometheus Metrics

Key metrics available at https://congress-metrics.local.team-skynet.io:

- `http_requests_total` - API request counts
- `http_request_duration_seconds` - Response times
- `pg_stat_database_*` - Database metrics
- `redis_*` - Cache metrics
- `congress_data_fetcher_*` - Data collection metrics

### Log Aggregation

Logs are collected via Filebeat and can be configured to send to:
- Elasticsearch/Kibana stack
- External log management services
- Local file storage with rotation

## Backup and Recovery

### Automated Backups

Backups run automatically via cron schedule:
- **Database**: Daily at 1 AM
- **Application Data**: Daily at 1 AM
- **Retention**: 30 days local, configurable S3

### Manual Backup

```bash
# Create immediate backup
./scripts/backup-prod.sh backup

# Verify backup integrity
./scripts/backup-prod.sh verify

# List available backups
./scripts/restore-prod.sh list
```

### Restore Procedures

```bash
# List available backups
./scripts/restore-prod.sh list

# Restore from specific backup
./scripts/restore-prod.sh restore 20241201_143022

# Restore latest backup
./scripts/restore-prod.sh restore-latest --force

# Download and restore from S3
./scripts/restore-prod.sh restore 20241201_143022 --from-s3
```

## Scaling and Performance

### Horizontal Scaling

1. **Backend API**: Increase replica count in `docker-compose.prod.yml`
2. **Database**: Configure read replicas for read-heavy workloads
3. **Cache**: Set up Redis cluster for high availability
4. **Frontend**: Use CDN for static asset delivery

### Performance Tuning

#### Database Optimization

```sql
-- Monitor slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'your_table';
```

#### Redis Optimization

Monitor Redis performance:
```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli info memory
docker-compose -f docker-compose.prod.yml exec redis redis-cli info stats
```

### Auto-scaling Configuration

For cloud deployments, configure auto-scaling based on:
- CPU utilization > 70%
- Memory utilization > 80%
- API response time > 1 second
- Queue length > 100 items

## Security Considerations

### Network Security

- All services communicate via private Docker networks
- Only necessary ports exposed through Traefik
- SSL/TLS termination at reverse proxy level

### Application Security

- CORS configured for specific origins
- Security headers enforced by nginx
- Input validation on all API endpoints
- Rate limiting on API and frontend

### Data Security

- Database encrypted at rest
- Redis password protected
- Backup encryption enabled
- Secrets managed via environment variables

### Security Updates

```bash
# Update Docker images monthly
docker-compose -f docker-compose.prod.yml pull
./scripts/deploy-production.sh deploy

# Monitor for security vulnerabilities
./scripts/security-scan.sh
```

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check service logs
docker-compose -f docker-compose.prod.yml logs -f [service-name]

# Check service health
docker-compose -f docker-compose.prod.yml ps

# Restart specific service
docker-compose -f docker-compose.prod.yml restart [service-name]
```

#### Database Connection Issues

```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U congress_app

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Access database directly
docker-compose -f docker-compose.prod.yml exec postgres psql -U congress_app -d congress_transparency
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check disk space
df -h

# Monitor API performance
curl -w "@curl-format.txt" -s https://congress-api.local.team-skynet.io/health
```

### Emergency Procedures

#### Complete System Recovery

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restore from backup
./scripts/restore-prod.sh restore-latest --force

# Restart services
./scripts/deploy-production.sh deploy
```

#### Database Recovery

```bash
# Create emergency backup
./scripts/backup-prod.sh backup

# Restore database only
./scripts/restore-prod.sh restore [timestamp] --data-only

# Verify integrity
psql -h localhost -U congress_app -d congress_transparency -c "SELECT COUNT(*) FROM members;"
```

## Maintenance

### Regular Maintenance Tasks

#### Weekly

- Review application logs for errors
- Check disk space and cleanup old logs
- Verify backup integrity
- Update security patches

#### Monthly

- Update Docker images
- Review performance metrics
- Rotate SSL certificates if needed
- Review and update monitoring alerts

#### Quarterly

- Review and update security configurations
- Performance optimization review
- Disaster recovery testing
- Documentation updates

### Maintenance Windows

Schedule maintenance during low-traffic periods:

```bash
# Enable maintenance mode
./scripts/maintenance-mode.sh enable

# Perform updates
./scripts/deploy-production.sh deploy

# Disable maintenance mode
./scripts/maintenance-mode.sh disable
```

## CI/CD Pipeline

### GitHub Actions Workflow

The deployment pipeline includes:

1. **Code Quality**: Linting, type checking, security scanning
2. **Testing**: Unit tests, integration tests, frontend builds
3. **Building**: Docker image creation and vulnerability scanning
4. **Deployment**: Automated deployment to staging and production
5. **Monitoring**: Post-deployment health checks and notifications

### Manual Deployment

```bash
# Deploy to staging
git push origin develop

# Deploy to production
git push origin main

# Deploy specific version
git tag v1.0.0
git push origin v1.0.0
```

## Support and Documentation

### Additional Resources

- [API Documentation](API.md)
- [Database Schema](DATABASE_README.md)
- [Monitoring Setup](monitoring/README.md)
- [Security Guidelines](SECURITY.md)

### Getting Help

1. Check application logs first
2. Review this documentation
3. Search existing GitHub issues
4. Create new issue with:
   - Environment details
   - Error messages
   - Steps to reproduce
   - Expected vs actual behavior

### Emergency Contacts

- **System Administrator**: [contact information]
- **DevOps Team**: [contact information]
- **On-call Support**: [contact information]

---

## Quick Reference

### Essential Commands

```bash
# Deploy production
./scripts/deploy-production.sh deploy

# Check status
./scripts/deploy-production.sh status

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Backup now
./scripts/backup-prod.sh backup

# Restore latest
./scripts/restore-prod.sh restore-latest

# Health check
./scripts/deploy-production.sh health

# Scale service
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Key File Locations

- **Configuration**: `.env.production.local`
- **Compose File**: `docker-compose.prod.yml`
- **Backups**: `/opt/congress-platform/backups/`
- **Data**: `/opt/congress-platform/data/`
- **Logs**: `/opt/congress-platform/logs/`
- **Scripts**: `./scripts/`