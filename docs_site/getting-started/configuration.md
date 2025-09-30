# Configuration Guide

## Overview

This guide covers the configuration of MusicChartsAI, including API keys, environment variables, and system settings.

## Environment Configuration

### Required Environment Variables

Create a `.env` file in your project root with these variables:

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
```

## API Configuration

### Soundcharts API Setup

1. **Get API Credentials**:
   - Visit [Soundcharts Developer Portal](https://customer.api.soundcharts.com)
   - Create an account and request API access
   - Obtain your `APP_ID` and `API_KEY`

2. **Configure in Django**:
   ```python
   # config/settings.py
   SOUNDCHARTS_APP_ID = os.getenv("SOUNDCHARTS_APP_ID")
   SOUNDCHARTS_API_KEY = os.getenv("SOUNDCHARTS_API_KEY")
   SOUNDCHARTS_API_URL = os.getenv("SOUNDCHARTS_API_URL", "https://customer.api.soundcharts.com")
   ```

### ACRCloud API Setup

1. **Get API Credentials**:
   - Visit [ACRCloud Console](https://console.acrcloud.com)
   - Create a project and get API credentials
   - Obtain `API_KEY`, `API_SECRET`, and `API_URL`

2. **Configure in Django**:
   ```python
   # config/settings.py
   ACR_CLOUD_API_KEY = os.getenv("ACR_CLOUD_API_KEY")
   ACR_CLOUD_API_SECRET = os.getenv("ACR_CLOUD_API_SECRET")
   ACR_CLOUD_API_URL = os.getenv("ACR_CLOUD_API_URL")
   ```

## Database Configuration

### SQLite (Default)
No additional configuration needed for development.

### PostgreSQL (Production)
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb musicchartsai
sudo -u postgres createuser --interactive

# Update settings
DATABASE_URL=postgresql://username:password@localhost:5432/musicchartsai
```

## Celery Configuration

### Redis Setup
```bash
# Install Redis
sudo apt install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test connection
redis-cli ping
```

### Celery Worker Configuration
```python
# config/settings.py
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER", "redis://localhost:6379")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BROKER", "redis://localhost:6379")
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
```

## Email Configuration

### SMTP Setup
```bash
# Add to .env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## File Storage Configuration

### Local Storage (Default)
Files stored in `media/` directory.

### AWS S3 (Production)
```bash
# Add to .env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## Security Configuration

### Production Settings
```python
# config/settings.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

## Logging Configuration

### Development Logging
```python
# config/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

### Production Logging
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/musicchartsai.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

## Verification

### Test Configuration
```bash
# Test database connection
python manage.py dbshell

# Test Celery connection
celery -A config inspect active

# Test API connections
python manage.py shell
>>> from apps.soundcharts.services import SoundchartsService
>>> service = SoundchartsService()
>>> service.test_connection()
```

### Configuration Checklist

- [ ] Environment variables set
- [ ] Database connection working
- [ ] Redis/Celery running
- [ ] API keys configured
- [ ] Email settings tested
- [ ] File storage configured
- [ ] Security settings applied
- [ ] Logging configured

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check database credentials
   - Ensure database server is running
   - Verify network connectivity

2. **Celery Worker Not Starting**
   - Check Redis connection
   - Verify Celery configuration
   - Check worker logs

3. **API Calls Failing**
   - Verify API keys are correct
   - Check API endpoint URLs
   - Test network connectivity

4. **File Upload Issues**
   - Check file permissions
   - Verify storage configuration
   - Check disk space

---

**Next Steps**: [Quick Start Guide](quick-start.md) or [Feature Overview](../features/overview.md)
