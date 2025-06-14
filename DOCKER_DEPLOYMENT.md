# Docker Deployment Guide

## Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env
```

### 2. Build and Run
```bash
# Build and start the application
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access Application
- **Dashboard**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

## Configuration

### Required Environment Variables
- `STRAVA_CLIENT_ID` - Your Strava application client ID
- `STRAVA_CLIENT_SECRET` - Your Strava application secret  
- `STRAVA_CALLBACK_URL` - OAuth callback URL
- `GEMINI_API_KEY` - Google Gemini API key for AI features

### Optional Configuration
- `SESSION_SECRET` - Custom session encryption key
- `JWT_SECRET` - Custom JWT signing key
- `DATABASE_URL` - PostgreSQL connection string (defaults to SQLite)
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Database Options

### SQLite (Default)
No additional setup required. Data persists in Docker volume.

### PostgreSQL (Optional)
Uncomment PostgreSQL service in `docker-compose.yml`:
```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: marathon_db
    POSTGRES_USER: marathon_user
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

Set `DATABASE_URL` in `.env`:
```bash
DATABASE_URL=postgresql://marathon_user:password@postgres:5432/marathon_db
```

## Production Deployment

### Security Considerations
- Generate strong secrets for `SESSION_SECRET` and `JWT_SECRET`
- Use environment-specific callback URLs
- Enable HTTPS in production
- Consider using external database service

### Scaling Options
```bash
# Scale to multiple instances
docker-compose up --scale marathon-dashboard=3

# Add load balancer (nginx example)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### Health Monitoring
Built-in health checks monitor application status:
- Database connectivity
- Core service availability
- Resource utilization

## Data Persistence

### Volumes
- `marathon_data` - SQLite database and application data
- `marathon_logs` - Application logs and monitoring data

### Backup
```bash
# Backup application data
docker run --rm -v marathon-training-dashboard_marathon_data:/data -v $(pwd):/backup alpine tar czf /backup/marathon_backup.tar.gz /data

# Restore from backup
docker run --rm -v marathon-training-dashboard_marathon_data:/data -v $(pwd):/backup alpine tar xzf /backup/marathon_backup.tar.gz -C /
```

## Troubleshooting

### Common Issues
1. **Port conflicts**: Change port mapping in `docker-compose.yml`
2. **Permission errors**: Ensure proper file permissions
3. **API failures**: Verify API keys in `.env` file
4. **Database issues**: Check volume mounts and permissions

### Logs
```bash
# View application logs
docker-compose logs marathon-dashboard

# Follow logs in real-time
docker-compose logs -f marathon-dashboard

# View specific service logs
docker-compose logs postgres
```

### Container Management
```bash
# Restart services
docker-compose restart

# Stop services
docker-compose down

# Clean up (removes containers and networks)
docker-compose down --volumes
```

## Performance Optimization

### Resource Limits
Add to `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

### Caching
Consider adding Redis for production:
```yaml
redis:
  image: redis:7-alpine
  restart: unless-stopped
```

## API Integration

### Strava Setup
1. Create Strava application at https://www.strava.com/settings/api
2. Set callback URL to your domain: `https://yourdomain.com/api/auth/strava/callback`
3. Add client ID and secret to `.env`

### Gemini AI Setup
1. Get API key from Google AI Studio
2. Add `GEMINI_API_KEY` to `.env`
3. Verify API access in application logs

The containerized application provides the same advanced features as the development version:
- Machine learning injury prediction
- AI-powered race recommendations
- Real-time Strava synchronization
- Advanced training analytics
- Senior athlete optimization