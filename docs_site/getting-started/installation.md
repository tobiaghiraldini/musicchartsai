# Installation Guide

## Prerequisites

Before installing MusicChartsAI, ensure you have the following prerequisites:

### System Requirements

- **Python**: 3.13 or higher
- **Node.js**: 22.0.0 or higher
- **Redis**: 7.0 or higher (for Celery message broker)
- **Database**: SQLite (default), PostgreSQL, or MySQL
- **Operating System**: Linux, macOS, or Windows

### Required Tools

- **Git**: For cloning the repository
- **pip**: Python package manager
- **npm**: Node.js package manager
- **Virtual Environment**: Python virtual environment (recommended)

## Installation Methods

### Method 1: Local Development Setup

#### Step 1: Clone the Repository

```bash
git clone https://github.com/your-repo/musicchartsai.git
cd musicchartsai
```

#### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Install Node.js Dependencies

```bash
npm install
```

#### Step 5: Environment Configuration

```bash
# Copy environment template
cp env.sample .env

# Edit environment variables
nano .env  # or use your preferred editor
```

#### Step 6: Database Setup

```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --no-input
```

#### Step 7: Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
celery -A config worker -l info -B

# Terminal 3: Start Django development server
python manage.py runserver

# Terminal 4: Start frontend build (development)
npm run dev
```

### Method 2: Docker Setup

#### Step 1: Clone Repository

```bash
git clone https://github.com/your-repo/musicchartsai.git
cd musicchartsai
```

#### Step 2: Environment Configuration

```bash
cp env.sample .env
# Edit .env file with your configuration
```

#### Step 3: Build and Start Services

```bash
# Build and start all services
docker-compose up --build

# Or start specific services
docker-compose up appseed-app
docker-compose up celery
docker-compose up redis
```

#### Step 4: Database Setup

```bash
# Run migrations
docker-compose exec appseed-app python manage.py migrate

# Create superuser
docker-compose exec appseed-app python manage.py createsuperuser
```

### Method 3: Production Deployment

#### Using Render (One-Click Deploy)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

#### Manual Production Setup

##### Prerequisites for Production

- **Linux Server**: Ubuntu 20.04+ or CentOS 8+
- **Domain Name**: Configured DNS pointing to your server
- **SSL Certificate**: For HTTPS (Let's Encrypt recommended)
- **Process Manager**: PM2 or Supervisor for process management

##### Step 1: Server Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.13 python3.13-venv python3.13-dev \
    nodejs npm redis-server postgresql postgresql-contrib \
    nginx git build-essential

# Install pyenv (optional, for Python version management)
curl https://pyenv.run | bash
```

##### Step 2: Application Setup

```bash
# Clone repository
git clone https://github.com/your-repo/musicchartsai.git
cd musicchartsai

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
npm install
```

##### Step 3: Database Configuration

```bash
# Configure PostgreSQL
sudo -u postgres createuser --interactive
sudo -u postgres createdb musicchartsai

# Update settings for production
# Edit config/settings.py to use PostgreSQL
```

##### Step 4: Production Build

```bash
# Build frontend assets
npm run build

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
```

##### Step 5: Process Management

```bash
# Install Supervisor
sudo apt install supervisor

# Create supervisor configuration
sudo nano /etc/supervisor/conf.d/musicchartsai.conf
```

Supervisor configuration:

```ini
[program:musicchartsai]
command=/path/to/musicchartsai/venv/bin/gunicorn config.wsgi:application
directory=/path/to/musicchartsai
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/musicchartsai.log

[program:celery-worker]
command=/path/to/musicchartsai/venv/bin/celery -A config worker -l info
directory=/path/to/musicchartsai
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery-worker.log

[program:celery-beat]
command=/path/to/musicchartsai/venv/bin/celery -A config beat -l info
directory=/path/to/musicchartsai
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery-beat.log
```

##### Step 6: Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/musicchartsai
```

Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/musicchartsai/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/musicchartsai/media/;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/musicchartsai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/musicchartsai

# Celery Configuration
CELERY_BROKER=redis://localhost:6379
REDIS_URL=redis://localhost:6379

# API Keys
SOUNDCHARTS_APP_ID=your-soundcharts-app-id
SOUNDCHARTS_API_KEY=your-soundcharts-api-key
SOUNDCHARTS_API_URL=https://customer.api.soundcharts.com

ACR_CLOUD_API_KEY=your-acrcloud-api-key
ACR_CLOUD_API_SECRET=your-acrcloud-api-secret
ACR_CLOUD_API_URL=your-acrcloud-api-url

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# File Storage (Optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket
AWS_S3_REGION_NAME=us-east-1
```

### Optional Environment Variables

```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/musicchartsai.log

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Performance
CACHE_URL=redis://localhost:6379/1
SESSION_ENGINE=django.contrib.sessions.backends.cache
```

## Verification

### Check Installation

After installation, verify everything is working:

#### 1. Django Server

```bash
python manage.py runserver
# Visit http://localhost:8000
```

#### 2. Celery Worker

```bash
celery -A config worker -l info
# Should show worker started successfully
```

#### 3. Redis Connection

```bash
redis-cli ping
# Should return PONG
```

#### 4. Database Connection

```bash
python manage.py dbshell
# Should connect to database successfully
```

#### 5. Static Files

```bash
python manage.py collectstatic --no-input
# Should collect all static files without errors
```

### Test API Endpoints

```bash
# Test Soundcharts API
curl -H "Authorization: Bearer your-api-key" \
     https://customer.api.soundcharts.com/api/v2/track/7d534228-5165-11e9-9375-549f35161576

# Test ACRCloud API
curl -X POST "your-acrcloud-api-url" \
     -H "Content-Type: application/json" \
     -d '{"api_key": "your-api-key"}'
```

## Troubleshooting

### Common Issues

#### 1. Python Version Issues

```bash
# Check Python version
python --version

# If wrong version, use pyenv
pyenv install 3.13.0
pyenv local 3.13.0
```

#### 2. Node.js Version Issues

```bash
# Check Node.js version
node --version

# If wrong version, use nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 22.0.0
nvm use 22.0.0
```

#### 3. Redis Connection Issues

```bash
# Check Redis status
sudo systemctl status redis

# Start Redis if not running
sudo systemctl start redis
sudo systemctl enable redis
```

#### 4. Database Migration Issues

```bash
# Reset migrations (development only)
rm apps/*/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
```

#### 5. Static Files Issues

```bash
# Check static files configuration
python manage.py findstatic admin/css/base.css

# Rebuild static files
rm -rf staticfiles/
python manage.py collectstatic --no-input
```

#### 6. Celery Worker Issues

```bash
# Check Celery status
celery -A config inspect active

# Restart Celery worker
pkill -f celery
celery -A config worker -l info -B
```

### Log Files

Check these log files for errors:

- **Django**: `logs/django.log`
- **Celery**: `logs/celery.log`
- **Nginx**: `/var/log/nginx/error.log`
- **System**: `/var/log/syslog`

### Performance Issues

#### 1. Slow Database Queries

```bash
# Enable query logging
# Add to settings.py:
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

#### 2. Memory Issues

```bash
# Monitor memory usage
htop
free -h

# Optimize Celery worker memory
# Add to settings.py:
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 200000  # 200MB
```

## Next Steps

After successful installation:

1. **[Configuration Guide](configuration.md)** - Configure API keys and settings
2. **[Quick Start Guide](quick-start.md)** - Run your first data sync
3. **[Feature Documentation](../features/overview.md)** - Learn about platform features
4. **[Admin Guide](../admin/dashboard-overview.md)** - Set up administrative functions

## Support

If you encounter issues during installation:

1. **Check the logs** for specific error messages
2. **Verify prerequisites** are installed correctly
3. **Review environment variables** are set properly
4. **Check network connectivity** for API access
5. **Join our community** for additional support

---

**Ready to configure your installation?** Check out the [Configuration Guide](configuration.md) next!
