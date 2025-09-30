# Deployment Procedure for Music Charts AI

This document provides step-by-step instructions for deploying the Music Charts AI Django application on Ubuntu 22.04 using the automated deployment script and manual configurations.

## Overview

The deployment process includes:
- Automated deployment script (`deploy.sh`)
- Production Gunicorn configuration
- Apache2 virtual host setup
- Systemd service configuration
- SSL/HTTPS setup
- Monitoring and maintenance

## Prerequisites

Before starting the deployment, ensure you have:

1. **Ubuntu 22.04 server** with root/sudo access
2. **Domain name** pointing to your server
3. **PostgreSQL database** configured
4. **Redis server** running
5. **SSL certificates** (Let's Encrypt recommended)
6. **Required services** installed: Apache2, PostgreSQL, Redis, Gunicorn

## Step-by-Step Deployment

### 1. Server Preparation

#### Create Application User
```bash
# Create dedicated user for the application
sudo adduser --system --group --shell /bin/bash musiccharts
sudo mkdir -p /opt/musiccharts
sudo chown musiccharts:musiccharts /opt/musiccharts
```

#### Install System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev \
    build-essential \
    curl \
    git \
    apache2 \
    redis-server \
    postgresql-client

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Database Setup
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user (replace with your values)
CREATE DATABASE musiccharts_db;
CREATE USER musiccharts_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE musiccharts_db TO musiccharts_user;
ALTER USER musiccharts_user CREATEDB;
\q
```

### 2. Application Deployment

#### Upload Application Files
```bash
# Copy your application to the server
# Option 1: Using git clone
sudo -u musiccharts git clone <your-repo-url> /opt/musiccharts/app

# Option 2: Using scp from your local machine
scp -r /path/to/your/app user@server:/tmp/
sudo mv /tmp/app /opt/musiccharts/
sudo chown -R musiccharts:musiccharts /opt/musiccharts
```

#### Configure Environment Variables
```bash
# Copy and edit environment file
sudo -u musiccharts cp /opt/musiccharts/app/env.sample /opt/musiccharts/app/.env
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

# API Keys (configure as needed)
ACR_CLOUD_API_KEY=your_acr_cloud_key
ACR_CLOUD_API_SECRET=your_acr_cloud_secret
ACR_CLOUD_API_URL=your_acr_cloud_url

SOUNDCHARTS_APP_ID=your_soundcharts_app_id
SOUNDCHARTS_API_KEY=your_soundcharts_api_key
```

### 3. Run Automated Deployment

#### Make Script Executable
```bash
chmod +x /opt/musiccharts/app/deploy.sh
```

#### Execute Deployment
```bash
# Run full deployment
cd /opt/musiccharts/app
./deploy.sh deploy
```

The script will:
- Create necessary directories
- Install Python dependencies
- Build frontend assets
- Run Django checks and migrations
- Configure Gunicorn
- Setup systemd services
- Configure Apache
- Start all services
- Perform health checks

### 4. Manual Configuration Steps

#### Configure Apache Virtual Host
```bash
# Copy Apache configuration
sudo cp /opt/musiccharts/app/apache-vhost.conf /etc/apache2/sites-available/musiccharts.conf

# Edit the configuration file to update your domain
sudo nano /etc/apache2/sites-available/musiccharts.conf

# Enable required Apache modules
sudo a2enmod ssl
sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod proxy
sudo a2enmod proxy_http

# Enable the site
sudo a2ensite musiccharts.conf

# Disable default site
sudo a2dissite 000-default.conf

# Test Apache configuration
sudo apache2ctl configtest
```

#### Setup SSL Certificates

**Option A: Using Let's Encrypt (Recommended)**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-apache -y

# Obtain SSL certificate
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

**Option B: Using Your Own Certificates**
```bash
# Copy your certificates
sudo cp your-cert.crt /etc/ssl/certs/
sudo cp your-private.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/your-private.key

# Update Apache configuration with correct paths
sudo nano /etc/apache2/sites-available/musiccharts.conf
```

#### Setup Systemd Services
```bash
# Copy systemd service files
sudo cp /opt/musiccharts/app/systemd-services/*.service /etc/systemd/system/
sudo cp /opt/musiccharts/app/systemd-services/*.socket /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable musiccharts-gunicorn.socket
sudo systemctl start musiccharts-gunicorn.socket
sudo systemctl enable musiccharts-gunicorn
sudo systemctl start musiccharts-gunicorn
sudo systemctl enable musiccharts-celery
sudo systemctl start musiccharts-celery
sudo systemctl enable musiccharts-celerybeat
sudo systemctl start musiccharts-celerybeat

# Restart Apache
sudo systemctl restart apache2
```

### 5. Post-Deployment Configuration

#### Create Django Superuser
```bash
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py createsuperuser
```

#### Verify Deployment
```bash
# Check service status
./deploy.sh status

# Run health check
./deploy.sh health

# Check logs
./deploy.sh logs
```

#### Configure Firewall
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

## Service Management

### Using the Deployment Script

```bash
# Start all services
./deploy.sh start

# Stop all services
./deploy.sh stop

# Restart all services
./deploy.sh restart

# Check service status
./deploy.sh status

# View logs
./deploy.sh logs

# Run health check
./deploy.sh health

# Create backup
./deploy.sh backup
```

### Manual Service Management

```bash
# Gunicorn service
sudo systemctl start/stop/restart musiccharts-gunicorn
sudo systemctl status musiccharts-gunicorn

# Celery worker
sudo systemctl start/stop/restart musiccharts-celery
sudo systemctl status musiccharts-celery

# Celery beat
sudo systemctl start/stop/restart musiccharts-celerybeat
sudo systemctl status musiccharts-celerybeat

# Apache
sudo systemctl start/stop/restart apache2
sudo systemctl status apache2
```

## Monitoring and Maintenance

### Log Files
- Application logs: `/var/log/musiccharts/`
- Apache logs: `/var/log/apache2/`
- System logs: `/var/log/syslog`

### Health Monitoring
```bash
# Check Django application
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py check

# Check database connection
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py dbshell

# Check Redis connection
redis-cli ping

# Check service status
systemctl status musiccharts-gunicorn musiccharts-celery musiccharts-celerybeat apache2
```

### Backup Strategy
```bash
# Database backup
sudo -u postgres pg_dump musiccharts_db > /opt/musiccharts/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# Application backup
sudo -u musiccharts tar -czf /opt/musiccharts/backups/app_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /opt/musiccharts app/

# Media files backup
sudo -u musiccharts tar -czf /opt/musiccharts/backups/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /opt/musiccharts app/media/
```

## Troubleshooting

### Common Issues

1. **Permission Issues**
   ```bash
   sudo chown -R musiccharts:musiccharts /opt/musiccharts
   sudo chmod -R 755 /opt/musiccharts
   ```

2. **Database Connection Issues**
   - Verify PostgreSQL is running: `sudo systemctl status postgresql`
   - Check database credentials in `.env` file
   - Test connection: `psql -h localhost -U musiccharts_user -d musiccharts_db`

3. **Static Files Not Loading**
   - Check Apache configuration for static file serving
   - Verify `collectstatic` was run
   - Check file permissions

4. **SSL Certificate Issues**
   - Verify certificate paths in Apache configuration
   - Check certificate validity: `openssl x509 -in /path/to/cert -text -noout`

5. **Service Not Starting**
   - Check logs: `journalctl -u service-name -f`
   - Verify configuration files
   - Check for port conflicts

### Useful Commands

```bash
# View real-time logs
sudo tail -f /var/log/musiccharts/gunicorn-error.log
sudo tail -f /var/log/apache2/error.log

# Test Apache configuration
sudo apache2ctl configtest

# Check listening ports
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :8000

# Check disk space
df -h

# Check memory usage
free -h

# Check process status
ps aux | grep gunicorn
ps aux | grep celery
```

## Security Considerations

1. **File Permissions**: Ensure proper ownership and permissions
2. **Environment Variables**: Never commit `.env` files
3. **Firewall**: Configure UFW properly
4. **SSL**: Use strong SSL configuration
5. **Updates**: Keep system and dependencies updated
6. **Backups**: Implement regular backup strategy

## Performance Optimization

1. **Gunicorn Workers**: Adjust based on CPU cores
2. **Database**: Optimize PostgreSQL settings
3. **Caching**: Implement Redis caching
4. **Static Files**: Use CDN if needed
5. **Monitoring**: Implement application monitoring

---

For additional support, refer to the project documentation or contact the development team.
