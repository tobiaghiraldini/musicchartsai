# Docker Deployment

## Overview

Docker deployment provides a streamlined way to containerize and deploy the MusicChartsAI application. This guide covers Docker configuration, containerization, and deployment using Docker Compose for a complete multi-container setup.

## Docker Configuration

### Understanding Docker Configuration Files

MusicChartsAI uses two main configuration files for Docker deployment:

1. **`Dockerfile`** - Defines the application container image
2. **`docker-compose.yml`** - Orchestrates multi-container deployment

### Dockerfile Configuration

The `Dockerfile` defines a multi-stage build process:

```dockerfile
FROM python:3.13.6

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install Node.js 22 and npm
RUN set -uex; \
    apt-get update; \
    apt-get install -y ca-certificates curl gnupg; \
    mkdir -p /etc/apt/keyrings; \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
     | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg; \
    NODE_MAJOR=22; \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" \
     > /etc/apt/sources.list.d/nodesource.list; \
    apt-get update; \
    apt-get install nodejs -y;

# Install modules and build assets
RUN npm i
RUN npm run build

# Django setup
RUN python manage.py collectstatic --no-input
RUN python manage.py makemigrations
RUN python manage.py migrate

# Start application with Gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "config.wsgi"]
```

**Build Stages:**

1. **Python Environment Setup**
   - Uses Python 3.13.6 base image
   - Sets environment variables for optimal performance
   - Installs Python dependencies from requirements.txt

2. **Node.js Environment Setup**
   - Installs Node.js 22 and npm
   - Installs frontend dependencies
   - Builds webpack assets

3. **Application Preparation**
   - Collects Django static files
   - Creates and applies database migrations
   - Configures Gunicorn as the WSGI server

### Docker Compose Configuration

The `docker-compose.yml` orchestrates multiple services:

```yaml
version: "3.8"

services:
  # Main Django Application
  musiccharts-app:
    container_name: musiccharts_app
    restart: always
    build: .
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@db:5432/musiccharts_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
    networks:
      - app_network
      - db_network
    depends_on:
      - db
      - redis

  # PostgreSQL Database
  db:
    container_name: musiccharts_db
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: musiccharts_db
      POSTGRES_USER: musiccharts_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - db_network
    ports:
      - "5432:5432"

  # Redis Cache and Message Broker
  redis:
    container_name: musiccharts_redis
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    networks:
      - app_network
    ports:
      - "6379:6379"

  # Celery Worker
  celery-worker:
    container_name: musiccharts_celery_worker
    build: .
    restart: always
    command: celery -A config worker -l info
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@db:5432/musiccharts_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - ./media:/app/media
    networks:
      - app_network
      - db_network
    depends_on:
      - db
      - redis

  # Celery Beat Scheduler
  celery-beat:
    container_name: musiccharts_celery_beat
    build: .
    restart: always
    command: celery -A config beat -l info
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@db:5432/musiccharts_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - ./media:/app/media
    networks:
      - app_network
      - db_network
    depends_on:
      - db
      - redis

  # Nginx Reverse Proxy
  nginx:
    container_name: musiccharts_nginx
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./staticfiles:/var/www/static
      - ./media:/var/www/media
      - ./ssl:/etc/nginx/ssl
    networks:
      - app_network
    depends_on:
      - musiccharts-app

volumes:
  postgres_data:
  redis_data:

networks:
  app_network:
    driver: bridge
  db_network:
    driver: bridge
```

**Service Components:**

1. **musiccharts-app**: Main Django application
2. **db**: PostgreSQL database
3. **redis**: Redis cache and message broker
4. **celery-worker**: Background task processing
5. **celery-beat**: Scheduled task management
6. **nginx**: Reverse proxy and static file serving

## Environment Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
# Django Configuration
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database Configuration
DATABASE_URL=postgresql://musiccharts_user:secure_password@db:5432/musiccharts_db

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# API Keys
ACR_CLOUD_API_KEY=your_acr_cloud_key
ACR_CLOUD_API_SECRET=your_acr_cloud_secret
ACR_CLOUD_API_URL=your_acr_cloud_url

SOUNDCHARTS_APP_ID=your_soundcharts_app_id
SOUNDCHARTS_API_KEY=your_soundcharts_api_key

# Site Configuration
SITE_URL=http://localhost:8000
```

## Nginx Configuration

### Main Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;

error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    include /etc/nginx/conf.d/*.conf;
}
```

### Site Configuration

Create `nginx/conf.d/musiccharts.conf`:

```nginx
upstream django {
    server musiccharts-app:8000;
}

server {
    listen 80;
    server_name localhost yourdomain.com;

    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Django application
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Health check endpoint
    location /health/ {
        proxy_pass http://django;
        access_log off;
    }
}
```

## Deployment Commands

### Build and Start Services

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Database Operations

```bash
# Create superuser
docker-compose exec musiccharts-app python manage.py createsuperuser

# Run migrations
docker-compose exec musiccharts-app python manage.py migrate

# Collect static files
docker-compose exec musiccharts-app python manage.py collectstatic --noinput

# Create database backup
docker-compose exec db pg_dump -U musiccharts_user musiccharts_db > backup.sql
```

### Service Management

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: This will delete all data)
docker-compose down -v

# Restart specific service
docker-compose restart musiccharts-app

# Scale celery workers
docker-compose up --scale celery-worker=3 -d

# View service logs
docker-compose logs -f musiccharts-app
docker-compose logs -f celery-worker
docker-compose logs -f nginx
```

## Development vs Production

### Development Configuration

For development, use `docker-compose.dev.yml`:

```yaml
version: "3.8"

services:
  musiccharts-app:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - ./media:/app/media
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://user:password@db:5432/musiccharts_db
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: musiccharts_dev
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Development Commands:**

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Run tests
docker-compose -f docker-compose.dev.yml exec musiccharts-app python manage.py test

# Run Django shell
docker-compose -f docker-compose.dev.yml exec musiccharts-app python manage.py shell
```

### Production Configuration

For production, ensure:

1. **Security Settings**:
   - Set `DEBUG=False`
   - Use strong secret keys
   - Configure proper `ALLOWED_HOSTS`
   - Enable SSL/HTTPS

2. **Performance Settings**:
   - Use multiple Gunicorn workers
   - Configure Redis caching
   - Optimize database queries
   - Enable gzip compression

3. **Monitoring**:
   - Set up log aggregation
   - Monitor container health
   - Configure alerts
   - Regular backups

## SSL/HTTPS Configuration

### Using Let's Encrypt

```bash
# Install certbot
docker run -it --rm -v certbot-certs:/etc/letsencrypt -v certbot-webroot:/var/www/certbot certbot/certbot certonly --webroot -w /var/www/certbot -d yourdomain.com

# Update nginx configuration for HTTPS
# Add SSL configuration to nginx/conf.d/musiccharts.conf
```

### SSL Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rest of your configuration...
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring and Logging

### Container Monitoring

```bash
# Monitor resource usage
docker stats

# Check container health
docker-compose exec musiccharts-app python manage.py check

# View application logs
docker-compose logs --tail=100 -f musiccharts-app
```

### Log Management

```bash
# Configure log rotation
# Add to docker-compose.yml:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Health Checks

Add health checks to your Dockerfile:

```dockerfile
# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U musiccharts_user musiccharts_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T db psql -U musiccharts_user musiccharts_db < backup_file.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v musiccharts_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v musiccharts_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Troubleshooting

### Common Issues

1. **Container Won't Start**
   ```bash
   # Check logs
   docker-compose logs musiccharts-app
   
   # Check configuration
   docker-compose config
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   docker-compose exec musiccharts-app python manage.py dbshell
   
   # Check database status
   docker-compose exec db pg_isready -U musiccharts_user
   ```

3. **Static Files Not Loading**
   ```bash
   # Collect static files
   docker-compose exec musiccharts-app python manage.py collectstatic --noinput
   
   # Check nginx configuration
   docker-compose exec nginx nginx -t
   ```

4. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   docker-compose exec musiccharts-app chown -R www-data:www-data /app/staticfiles
   ```

### Useful Commands

```bash
# Clean up unused containers and images
docker system prune -a

# View container resource usage
docker-compose top

# Execute commands in running container
docker-compose exec musiccharts-app bash

# Restart services in dependency order
docker-compose restart

# Scale services
docker-compose up --scale celery-worker=3 -d
```

## Best Practices

### Security

1. **Use non-root users** in containers
2. **Keep images updated** with security patches
3. **Use secrets management** for sensitive data
4. **Enable firewall** and network security
5. **Regular security audits** of containers

### Performance

1. **Optimize Dockerfile** layers
2. **Use multi-stage builds** to reduce image size
3. **Configure resource limits** for containers
4. **Use health checks** for better monitoring
5. **Implement proper caching** strategies

### Maintenance

1. **Regular backups** of data and volumes
2. **Monitor resource usage** and logs
3. **Update dependencies** regularly
4. **Clean up unused** containers and images
5. **Document configuration** changes

## Conclusion

Docker deployment provides a robust, scalable solution for deploying MusicChartsAI. With proper configuration and monitoring, it ensures consistent deployment across different environments while maintaining high availability and performance.

For additional support, refer to the project documentation or contact the development team.
