# Ubuntu 22.04 Deployment Guide

This guide provides comprehensive instructions for deploying the Music Charts AI Django application on Ubuntu 22.04 with Apache2, PostgreSQL, Redis, SSL, and Gunicorn.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Deployment](#application-deployment)
4. [Configuration Files](#configuration-files)
5. [SSL Configuration](#ssl-configuration)
6. [Service Management](#service-management)
7. [Monitoring and Logs](#monitoring-and-logs)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Ubuntu 22.04 LTS
- Minimum 2GB RAM (4GB recommended)
- 20GB free disk space
- Root or sudo access

### Installed Services
- Apache2
- PostgreSQL
- Redis
- SSL certificates
- Gunicorn

## Server Setup

### 1. Create Application User

```bash
# Create dedicated user for the application
sudo adduser --system --group --shell /bin/bash musiccharts
sudo mkdir -p /opt/musiccharts
sudo chown musiccharts:musiccharts /opt/musiccharts
```

### 2. Install Python Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv python3-dev -y

# Install system dependencies for PostgreSQL
sudo apt install libpq-dev -y

# Install Node.js and npm for frontend build
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 3. Database Setup

```bash
# Connect to PostgreSQL as postgres user
sudo -u postgres psql

# Create database and user (replace with your actual values)
CREATE DATABASE musiccharts_db;
CREATE USER musiccharts_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE musiccharts_db TO musiccharts_user;
ALTER USER musiccharts_user CREATEDB;
\q
```

## Application Deployment

### 1. Deploy Application Code

```bash
# Clone or copy your application to the server
sudo -u musiccharts git clone <your-repo-url> /opt/musiccharts/app
# OR copy files using scp/rsync from your local machine

# Set proper ownership
sudo chown -R musiccharts:musiccharts /opt/musiccharts
```

### 2. Environment Configuration

```bash
# Create environment file
sudo -u musiccharts cp /opt/musiccharts/app/env.sample /opt/musiccharts/app/.env

# Edit environment variables
sudo -u musiccharts nano /opt/musiccharts/app/.env
```

**Required Environment Variables:**

```env
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here

# Database Configuration
DB_ENGINE=postgresql
DB_HOST=localhost
DB_NAME=musiccharts_db
DB_USERNAME=musiccharts_user
DB_PASS=your_secure_password
DB_PORT=5432

# Redis Configuration
CELERY_BROKER=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SSL Configuration
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True

# Site URL
SITE_URL=https://yourdomain.com

# API Keys (if applicable)
ACR_CLOUD_API_KEY=your_acr_cloud_key
ACR_CLOUD_API_SECRET=your_acr_cloud_secret
ACR_CLOUD_API_URL=your_acr_cloud_url

SOUNDCHARTS_APP_ID=your_soundcharts_app_id
SOUNDCHARTS_API_KEY=your_soundcharts_api_key
```

### 3. Python Virtual Environment Setup

```bash
# Create virtual environment
sudo -u musiccharts python3 -m venv /opt/musiccharts/venv

# Activate virtual environment and install dependencies
sudo -u musiccharts /opt/musiccharts/venv/bin/pip install --upgrade pip
sudo -u musiccharts /opt/musiccharts/venv/bin/pip install -r /opt/musiccharts/app/requirements.txt
```

### 4. Frontend Build

```bash
# Install Node.js dependencies and build
cd /opt/musiccharts/app
sudo -u musiccharts npm install
sudo -u musiccharts npm run build
```

### 5. Database Migration

```bash
# Run Django migrations
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py migrate

# Create superuser
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py createsuperuser

# Collect static files
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py collectstatic --noinput
```

## Configuration Files

### 1. Gunicorn Configuration

The application includes a `gunicorn-cfg.py` file. For production, we'll create an optimized version.

### 2. Systemd Service Files

Create systemd service files for Gunicorn and Celery to ensure proper service management.

### 3. Apache Virtual Host

Configure Apache to proxy requests to Gunicorn and serve static files.

## SSL Configuration

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-apache -y

# Obtain SSL certificate
sudo certbot --apache -d yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Manual SSL Configuration

If you have your own SSL certificates:

```bash
# Copy certificates to Apache directory
sudo cp your-cert.crt /etc/ssl/certs/
sudo cp your-private.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/your-private.key
```

## Service Management

### Starting Services

```bash
# Start and enable services
sudo systemctl start musiccharts-gunicorn
sudo systemctl enable musiccharts-gunicorn

sudo systemctl start musiccharts-celery
sudo systemctl enable musiccharts-celery

sudo systemctl start musiccharts-celerybeat
sudo systemctl enable musiccharts-celerybeat

# Restart Apache
sudo systemctl restart apache2
```

### Service Status

```bash
# Check service status
sudo systemctl status musiccharts-gunicorn
sudo systemctl status musiccharts-celery
sudo systemctl status musiccharts-celerybeat
sudo systemctl status apache2
```

## Monitoring and Logs

### Log Locations

- Application logs: `/var/log/musiccharts/`
- Apache logs: `/var/log/apache2/`
- System logs: `/var/log/syslog`

### Log Rotation

Configure log rotation to prevent disk space issues.

### Health Checks

Implement health check endpoints and monitoring.

## Troubleshooting

### Common Issues

1. **Permission Issues**: Ensure proper ownership of files and directories
2. **Database Connection**: Verify PostgreSQL is running and credentials are correct
3. **Static Files**: Check Apache configuration for static file serving
4. **SSL Issues**: Verify certificate validity and Apache SSL configuration

### Useful Commands

```bash
# Check Gunicorn processes
ps aux | grep gunicorn

# Check Django application
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py check

# Test database connection
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py dbshell

# Check Redis connection
redis-cli ping

# View Apache error logs
sudo tail -f /var/log/apache2/error.log

# View application logs
sudo tail -f /var/log/musiccharts/gunicorn.log
```

## Security Considerations

1. **Firewall**: Configure UFW to allow only necessary ports
2. **File Permissions**: Set restrictive permissions on sensitive files
3. **Environment Variables**: Never commit `.env` files to version control
4. **Regular Updates**: Keep system and application dependencies updated
5. **Backup**: Implement regular database and file backups

## Backup Strategy

### Database Backup

```bash
# Create backup script
sudo -u postgres pg_dump musiccharts_db > /opt/musiccharts/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql
```

### File Backup

```bash
# Backup application files
sudo tar -czf /opt/musiccharts/backups/app_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/musiccharts/app
```

## Performance Optimization

1. **Gunicorn Workers**: Adjust worker count based on CPU cores
2. **Database**: Optimize PostgreSQL configuration
3. **Caching**: Implement Redis caching for better performance
4. **Static Files**: Use CDN for static file delivery
5. **Monitoring**: Implement application performance monitoring

---

For additional support or questions, refer to the project documentation or contact the development team.
