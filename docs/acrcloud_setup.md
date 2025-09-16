# ACRCloud Integration Setup Guide

## Prerequisites

Before setting up the ACRCloud integration, ensure you have:

1. **Django Project**: Working Django project with Celery configured
2. **ACRCloud Account**: Active ACRCloud account with API access
3. **Redis/Broker**: Celery message broker (Redis recommended)
4. **File Storage**: Sufficient storage for audio files
5. **Python Dependencies**: Required packages installed

## Step 1: Install Dependencies

Add the following to your `requirements.txt`:

```txt
# ACRCloud integration dependencies
celery>=5.3.0
redis>=4.5.0
python-dotenv>=1.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Step 2: Environment Configuration

### ACRCloud API Setup

1. **Create ACRCloud Account**:
   - Visit [ACRCloud Console](https://console.acrcloud.com)
   - Sign up for an account
   - Verify your email

2. **Get API Credentials**:
   - Navigate to API Management
   - Create a new API key
   - Note down the following:
     - Base URL (e.g., `https://api-eu-west-1.acrcloud.com`)
     - Bearer Token
     - Container ID (for File Scanning)
     - Identify Host (e.g., `identify-eu-west-1.acrcloud.com`)
     - Access Key and Secret (for Identification API)

3. **Configure Environment Variables**:
   Add to your `.env` file:
   ```bash
   # ACRCloud Configuration
   ACR_CLOUD_API_KEY=your_api_key
   ACR_CLOUD_API_SECRET=your_api_secret
   ACR_CLOUD_API_URL=https://api-eu-west-1.acrcloud.com
   
   # Optional: Email notifications
   ACRCLOUD_NOTIFICATION_EMAIL=admin@example.com
   ```

## Step 3: Django Configuration

### 1. Add ACRCloud App

Ensure `acrcloud` is in your `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'acrcloud',
]
```

### 2. Media Configuration

Configure media file handling:

```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
```

### 3. Celery Configuration

Ensure Celery is properly configured:

```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
```

### 4. Email Configuration (Optional)

Configure email for notifications:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

## Step 4: Database Setup

### 1. Create Migrations

```bash
python manage.py makemigrations acrcloud
```

### 2. Apply Migrations

```bash
python manage.py migrate acrcloud
```

### 3. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

## Step 5: ACRCloud Configuration

### 1. Access Django Admin

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to `/admin/`

3. Login with your superuser credentials

### 2. Configure ACRCloud Settings

1. Go to **ACRCloud Configurations**
2. Click **Add ACRCloud Configuration**
3. Fill in the required fields:
   - **Name**: `Production` (or any descriptive name)
   - **Base URL**: Your ACRCloud API base URL
   - **Bearer Token**: Your ACRCloud bearer token
   - **Container ID**: Your File Scanning container ID
   - **Identify Host**: Your identification API host
   - **Identify Access Key**: Your identification API access key
   - **Identify Access Secret**: Your identification API secret
   - **Is Active**: Check this box
4. Click **Save**

## Step 6: Celery Worker Setup

### 1. Start Celery Worker

In a separate terminal:

```bash
celery -A config worker -l info
```

### 2. Start Celery Beat (Optional)

For scheduled tasks:

```bash
celery -A config beat -l info
```

### 3. Monitor Celery (Optional)

```bash
celery -A config flower
```

## Step 7: Test the Integration

### 1. Access User Interface

1. Navigate to `/acrcloud/upload/`
2. Upload a test audio file
3. Monitor the analysis process
4. View the results

### 2. Check Admin Interface

1. Go to `/admin/acrcloud/`
2. Verify songs are being created
3. Check analysis status
4. Review generated reports

### 3. Test API Endpoints

```bash
# Test file upload
curl -X POST http://localhost:8000/acrcloud/api/upload/ \
  -F "filepond=@test_audio.mp3"

# Test analysis status
curl http://localhost:8000/acrcloud/api/song/<song_id>/status/
```

## Step 8: Production Deployment

### 1. Environment Variables

Set production environment variables:

```bash
# Production ACRCloud settings
ACR_CLOUD_API_KEY=production_api_key
ACR_CLOUD_API_SECRET=production_api_secret
ACR_CLOUD_API_URL=https://api-eu-west-1.acrcloud.com

# Production email settings
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-password
```

### 2. Static Files

Collect static files:

```bash
python manage.py collectstatic
```

### 3. Database

Run migrations in production:

```bash
python manage.py migrate acrcloud
```

### 4. Celery Workers

Start production Celery workers:

```bash
# Using systemd (recommended)
sudo systemctl start celery-worker
sudo systemctl enable celery-worker

# Or using supervisor
supervisorctl start celery-worker
```

### 5. File Storage

Configure production file storage:

```python
# settings.py
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# Or use cloud storage like AWS S3
```

## Troubleshooting

### Common Issues

#### 1. Celery Worker Not Starting

**Error**: `ModuleNotFoundError: No module named 'acrcloud'`

**Solution**: Ensure the ACRCloud app is in `INSTALLED_APPS` and the Python path is correct.

#### 2. ACRCloud API Errors

**Error**: `401 Unauthorized`

**Solution**: Check your API credentials and ensure they're correctly configured.

#### 3. File Upload Failures

**Error**: `413 Request Entity Too Large`

**Solution**: Increase file upload limits in Django settings.

#### 4. Analysis Not Starting

**Error**: Analysis stuck in "uploaded" status

**Solution**: Check Celery worker status and logs.

### Debug Mode

Enable debug logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'acrcloud': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Health Checks

Create a health check endpoint:

```python
# views.py
from django.http import JsonResponse
from celery import current_app

def health_check(request):
    # Check Celery
    celery_status = current_app.control.inspect().stats()
    
    # Check ACRCloud
    try:
        from .service import ACRCloudService
        service = ACRCloudService()
        acrcloud_status = "OK"
    except Exception as e:
        acrcloud_status = f"Error: {str(e)}"
    
    return JsonResponse({
        'celery': 'OK' if celery_status else 'Error',
        'acrcloud': acrcloud_status,
        'database': 'OK'  # Add database check if needed
    })
```

## Security Considerations

### 1. File Upload Security

- Implement virus scanning
- Validate file types server-side
- Set appropriate file size limits
- Use secure file storage

### 2. API Security

- Enable CSRF protection
- Implement rate limiting
- Use HTTPS in production
- Validate all inputs

### 3. Data Privacy

- Implement user data isolation
- Use secure credential storage
- Enable audit logging
- Set data retention policies

## Monitoring

### 1. Log Monitoring

Monitor logs for:
- Analysis failures
- API errors
- Performance issues
- Security events

### 2. Performance Monitoring

Track:
- Analysis completion times
- File upload success rates
- API response times
- Database performance

### 3. Alerting

Set up alerts for:
- Analysis failures
- API quota exceeded
- Storage space low
- Worker process down

## Maintenance

### 1. Regular Tasks

- Clean up old analysis data
- Monitor API usage
- Update dependencies
- Review security settings

### 2. Backup Strategy

- Backup database regularly
- Backup uploaded files
- Backup configuration
- Test restore procedures

### 3. Updates

- Keep dependencies updated
- Monitor ACRCloud API changes
- Test updates in staging
- Plan maintenance windows

## Support

For additional support:

1. Check the troubleshooting section
2. Review ACRCloud documentation
3. Check Django and Celery documentation
4. Contact system administrator
5. Submit issue reports

## Next Steps

After successful setup:

1. Configure additional ACRCloud settings
2. Set up monitoring and alerting
3. Train users on the interface
4. Implement additional security measures
5. Plan for scaling and optimization
