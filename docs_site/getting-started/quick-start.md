# Quick Start Guide

## Overview

Welcome to MusicChartsAI! This quick start guide will help you get up and running with the music analytics platform in minutes. Whether you're setting up for development or production, this guide covers all the essential steps.

## Prerequisites

### System Requirements

**Development Environment**:
- Python 3.11+ 
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Git

**Production Environment**:
- Ubuntu 22.04 LTS (recommended)
- 2GB RAM minimum (4GB recommended)
- 20GB free disk space
- Domain name (for production deployment)

### Required Accounts

**External Services**:
- [ACRCloud Account](https://www.acrcloud.com/) - For audio analysis and fraud detection
- [SoundCharts Account](https://soundcharts.com/) - For music chart data
- [GitHub Account](https://github.com/) - For code repository and CI/CD
- [Render Account](https://render.com/) - For cloud deployment (optional)

## Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd rocket-django-main

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
# Install Node.js dependencies
npm install

# Build frontend assets
npm run build
```

### 3. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE musiccharts_db;
CREATE USER musiccharts_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE musiccharts_db TO musiccharts_user;
ALTER USER musiccharts_user CREATEDB;
\q

# Install and start Redis
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Django Configuration
DEBUG=True
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

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

# ACRCloud Configuration
ACR_CLOUD_API_KEY=your_acr_cloud_key
ACR_CLOUD_API_SECRET=your_acr_cloud_secret
ACR_CLOUD_API_URL=https://api-eu-west-1.acrcloud.com

# SoundCharts Configuration
SOUNDCHARTS_APP_ID=your_soundcharts_app_id
SOUNDCHARTS_API_KEY=your_soundcharts_api_key

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Site Configuration
SITE_URL=http://localhost:8000
```

### 5. Database Migration

```bash
# Run Django migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## Running the Application

### Development Mode

**Option 1: Using Django Development Server**

```bash
# Start Django development server
python manage.py runserver

# In separate terminals, start Celery services
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
```

**Option 2: Using Service Management Script**

```bash
# Make script executable
chmod +x scripts/start_services.sh

# Start all services
./scripts/start_services.sh start

# Check status
./scripts/start_services.sh status

# View logs
./scripts/start_services.sh logs
```

### Production Mode

**Using Systemd Services**:

```bash
# Enable and start services
sudo systemctl enable musiccharts-gunicorn
sudo systemctl enable musiccharts-celery
sudo systemctl enable musiccharts-celerybeat

sudo systemctl start musiccharts-gunicorn
sudo systemctl start musiccharts-celery
sudo systemctl start musiccharts-celerybeat

# Check status
sudo systemctl status musiccharts-gunicorn
sudo systemctl status musiccharts-celery
sudo systemctl status musiccharts-celerybeat
```

## Initial Configuration

### 1. Access Admin Interface

Navigate to `http://localhost:8000/admin/` and log in with your superuser credentials.

### 2. Configure ACRCloud

1. Go to **ACR Cloud** → **ACRCloud Config**
2. Click **Add ACRCloud Config**
3. Enter your ACRCloud credentials:
   - **API Key**: Your ACRCloud API key
   - **API Secret**: Your ACRCloud API secret
   - **API URL**: `https://api-eu-west-1.acrcloud.com`
4. Save the configuration

### 3. Configure SoundCharts

1. Go to **Soundcharts** → **Charts**
2. Click **Import from API** button
3. Configure import parameters:
   - **Limit**: Number of charts to import (start with 10)
   - **Offset**: Starting position (0 for first batch)
4. Click **Fetch Charts** to import initial chart data

### 4. Test Audio Analysis

1. Go to **ACR Cloud** → **Analyses**
2. Click **Add Analysis**
3. Upload a sample audio file
4. Verify the analysis completes successfully

## Key Features Overview

### 1. Music Chart Management

- **Chart Import**: Import charts from SoundCharts API
- **Rankings Sync**: Automated synchronization of chart rankings
- **Historical Data**: Complete historical chart data
- **Multi-platform Support**: Support for Spotify, Apple Music, YouTube, etc.

### 2. Audio Analysis

- **Fraud Detection**: Identify potential fraudulent content
- **Cover Detection**: Detect cover songs and remixes
- **Lyrics Analysis**: Analyze song lyrics for content
- **Audio Fingerprinting**: Create unique audio fingerprints

### 3. Analytics Dashboard

- **Real-time Charts**: Interactive charts with ApexCharts
- **Audience Analytics**: Track audience growth over time
- **Platform Comparison**: Compare performance across platforms
- **Trend Analysis**: Identify trending songs and artists

### 4. Admin Interface

- **Custom Ordering**: Business-logic based admin organization
- **Bulk Operations**: Efficient bulk data management
- **Progress Tracking**: Real-time progress monitoring
- **Error Handling**: Comprehensive error reporting

## Common Tasks

### Import Chart Data

```bash
# Import charts from SoundCharts API
python manage.py import_charts --limit 50

# Sync chart rankings
python manage.py sync_chart_rankings --chart-id 1

# Create sync schedule
python manage.py create_sync_schedule --chart-id 1 --frequency daily
```

### Fetch Track Metadata

```bash
# Fetch metadata for specific track
python manage.py fetch_track_metadata --track-uuid <uuid>

# Bulk metadata fetch
python manage.py fetch_track_metadata --bulk

# Fetch all tracks metadata
python manage.py fetch_track_metadata --all
```

### Manage Background Tasks

```bash
# Check Celery status
celery -A config inspect active

# Monitor task execution
celery -A config events

# Purge task queue
celery -A config purge
```

## Troubleshooting

### Common Issues

**1. Database Connection Error**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
python manage.py dbshell
```

**2. Redis Connection Error**:
```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connection
redis-cli ping
```

**3. Static Files Not Loading**:
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check file permissions
ls -la staticfiles/
```

**4. Celery Tasks Not Processing**:
```bash
# Check Celery worker status
ps aux | grep celery

# Restart Celery services
sudo systemctl restart musiccharts-celery
sudo systemctl restart musiccharts-celerybeat
```

### Debug Mode

Enable debug mode for detailed error information:

```env
# In .env file
DEBUG=True
```

### Log Files

**Application Logs**:
```bash
# View Django logs
tail -f logs/django.log

# View Celery logs
tail -f logs/celery-worker.log
tail -f logs/celery-beat.log

# View system logs
sudo journalctl -u musiccharts-gunicorn -f
```

## Next Steps

### 1. Explore the Documentation

- **Features**: Learn about advanced features and capabilities
- **API Reference**: Understand the REST API endpoints
- **Deployment**: Set up production deployment
- **Troubleshooting**: Resolve common issues

### 2. Customize the Application

- **Admin Interface**: Customize admin ordering and functionality
- **Charts**: Create custom charts and visualizations
- **Data Models**: Extend models for your specific needs
- **API Integration**: Add new API integrations

### 3. Production Deployment

- **Server Setup**: Configure production server
- **SSL Configuration**: Set up HTTPS
- **Monitoring**: Implement monitoring and alerting
- **Backup Strategy**: Create backup and recovery procedures

### 4. Advanced Configuration

- **Performance Tuning**: Optimize database and application performance
- **Security**: Implement security best practices
- **Scaling**: Plan for horizontal scaling
- **CI/CD**: Set up automated deployment pipelines

## Getting Help

### Documentation Resources

- **Development Guide**: Comprehensive development documentation
- **API Documentation**: Complete API reference
- **Deployment Guide**: Production deployment instructions
- **Troubleshooting Guide**: Common issues and solutions

### Support Channels

- **GitHub Issues**: Report bugs and request features
- **Community Forums**: Ask questions and get help
- **Professional Support**: Contact for commercial support

### Useful Commands

```bash
# Check Django configuration
python manage.py check

# Check database
python manage.py dbshell

# Check migrations
python manage.py showmigrations

# Check static files
python manage.py collectstatic --dry-run

# Check Celery
celery -A config inspect active

# Check Redis
redis-cli ping

# Check system resources
free -h
df -h
ps aux | grep python
```

## Conclusion

Congratulations! You've successfully set up MusicChartsAI. The platform is now ready for music data analysis, chart management, and audio processing. 

Key next steps:
1. **Configure External Services**: Set up ACRCloud and SoundCharts integrations
2. **Import Initial Data**: Import charts and track data
3. **Explore Features**: Test audio analysis and analytics dashboard
4. **Customize**: Adapt the platform to your specific needs
5. **Deploy**: Set up production deployment when ready

For detailed information about specific features and advanced configuration, refer to the comprehensive documentation in the `docs_site/` directory.