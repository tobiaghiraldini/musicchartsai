# Troubleshooting

## Overview

This comprehensive troubleshooting guide covers common issues, solutions, and debugging techniques for MusicChartsAI. The guide is organized by component and includes step-by-step solutions for development and production environments.

## Gunicorn Configuration Issues

### Common Gunicorn Errors

#### Permission Denied Errors

**Problem**: Gunicorn fails to start due to permission issues with log files, PID files, or user/group settings.

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied: '/var/log/musiccharts/gunicorn-error.log'
OSError: [Errno 13] Permission denied: '/var/run/musiccharts-gunicorn.pid'
```

**Solutions**:

1. **Use Simple Configuration (Recommended for Development)**:
```bash
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
```

2. **Fix Permissions for Production Config**:
```bash
# Create log directory
sudo mkdir -p /var/log/musiccharts
sudo chown $USER:$USER /var/log/musiccharts
sudo chmod 755 /var/log/musiccharts

# Create PID directory
sudo mkdir -p /var/run
sudo chown $USER:$USER /var/run
```

3. **Use Command Line Arguments**:
```bash
gunicorn --workers=2 --bind=0.0.0.0:8080 config.wsgi:application
```

#### Worker Process Failures

**Problem**: Gunicorn workers die unexpectedly.

**Symptoms**:
```
[ERROR] Worker (pid:1234) was sent SIGABRT signal!
[ERROR] Worker (pid:1234) did not respond to heartbeats
```

**Solutions**:

1. **Reduce Worker Count**:
```bash
gunicorn --workers=1 --bind=127.0.0.1:8080 config.wsgi:application
```

2. **Check Django Settings**:
```bash
python manage.py check --deploy
python manage.py check
```

3. **Test Django Directly**:
```bash
python manage.py runserver 127.0.0.1:8080
```

### Gunicorn Configuration Comparison

| Setting | Command Line | Simple Config | Production Config |
|---------|--------------|---------------|-------------------|
| Workers | 2 | 2 | CPU cores * 2 + 1 |
| Bind | 0.0.0.0:8080 | 127.0.0.1:8080 | 127.0.0.1:8080 |
| Logging | Default | Console | File-based |
| User/Group | Current user | Current user | musiccharts |
| PID File | No | No | Yes |

### Debugging Gunicorn Issues

#### Step 1: Test with Minimal Configuration
```bash
gunicorn --bind=127.0.0.1:8080 config.wsgi:application
```

#### Step 2: Add Workers Gradually
```bash
gunicorn --workers=1 --bind=127.0.0.1:8080 config.wsgi:application
gunicorn --workers=2 --bind=127.0.0.1:8080 config.wsgi:application
```

#### Step 3: Test Configuration File
```bash
# Check if config file is valid Python
python gunicorn-simple.conf.py

# Test with verbose logging
gunicorn --config gunicorn-simple.conf.py --log-level debug config.wsgi:application
```

## Static Files Issues

### Static Files Not Loading

**Problem**: CSS, JavaScript, and other static files are not loading properly.

**Symptoms**:
- Styling not applied
- JavaScript errors in browser console
- 404 errors for static files
- Files served as `text/html` instead of proper MIME types

**Solutions**:

1. **Collect Static Files**:
```bash
python manage.py collectstatic --noinput --clear
```

2. **Check Static Files Configuration**:
```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

3. **Fix File Permissions**:
```bash
# Set proper ownership (replace 'youruser' with actual user)
sudo chown -R youruser:www-data /path/to/staticfiles/
sudo chown -R youruser:www-data /path/to/media/

# Set proper permissions
sudo chmod -R 755 /path/to/staticfiles/
sudo chmod -R 755 /path/to/media/

# Ensure Apache can read the files
sudo chmod -R 644 /path/to/staticfiles/*
```

4. **Check Apache/Nginx Configuration**:
```apache
# Apache configuration with MIME types
Alias /static/ /path/to/staticfiles/
<Directory /path/to/staticfiles>
    Require all granted
    # Ensure proper MIME types
    AddType text/css .css
    AddType application/javascript .js
</Directory>
```

```nginx
# Nginx configuration
location /static/ {
    alias /path/to/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Content Security Policy (CSP) Issues

**Problem**: CSP blocks external resources like Google Fonts, GitHub buttons, or FilePond components.

**Symptoms**:
```
Refused to load the script 'https://unpkg.com/filepond.min.js'
Refused to load the stylesheet 'https://fonts.googleapis.com/css'
Refused to connect to 'https://api.github.com'
```

**Solutions**:

1. **Update CSP Configuration**:
```apache
# Apache CSP header with all required domains
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://buttons.github.io https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; font-src 'self' data: https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.github.com;"
```

2. **Test CSP Configuration**:
```bash
# Test Apache configuration
sudo apache2ctl configtest

# If test passes, restart Apache
sudo systemctl restart apache2

# Clear browser cache or use incognito mode
```

3. **Alternative: Host Resources Locally**:
```bash
# Download external resources locally
mkdir -p /path/to/static/vendor/filepond
cd /path/to/static/vendor/filepond

# Download FilePond files
wget https://unpkg.com/filepond/dist/filepond.min.css
wget https://unpkg.com/filepond/dist/filepond.min.js
wget https://unpkg.com/filepond-plugin-file-validate-type/dist/filepond-plugin-file-validate-type.min.js
wget https://unpkg.com/filepond-plugin-file-validate-size/dist/filepond-plugin-file-validate-size.min.js
```

4. **Development CSP (More Permissive)**:
```apache
# For development only - more permissive CSP
Header always set Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; font-src 'self' data: https:; img-src 'self' data: https:; connect-src 'self' https:;"
```

### Static Files Verification

**Test Static Files Directly**:
```bash
# Test if static files are accessible
curl -I https://yourdomain.com/static/dist/main.css
curl -I https://yourdomain.com/static/images/logo.png

# Check file sizes
du -sh /path/to/staticfiles/

# Verify specific files exist
ls -la /path/to/staticfiles/dist/main.css
ls -la /path/to/staticfiles/dist/main.bundle.js
```

**Check Apache Error Logs**:
```bash
# Monitor Apache error logs
sudo tail -f /var/log/apache2/error.log

# Check specific site error log
sudo tail -f /path/to/site/error.log
```

**Browser Testing**:
1. Open browser developer tools (F12)
2. Go to Network tab
3. Reload the page
4. Check if static files load with 200 status codes
5. Verify no 403 or 404 errors for static files

### Tailwind CSS Build Issues

**Problem**: Tailwind CSS styles not being generated or applied.

**Solutions**:

1. **Install Node.js Dependencies**:
```bash
npm install
npm run build
```

2. **Check Webpack Configuration**:
```javascript
// webpack.config.js
module.exports = {
    entry: './static/assets/index.js',
    output: {
        filename: '[name].bundle.js',
        path: path.resolve(__dirname, './static/dist'),
    },
};
```

3. **Check Tailwind Configuration**:
```javascript
// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.js',
    './node_modules/flowbite/**/*.js'
  ],
  plugins: [
    require('flowbite/plugin')
  ],
}
```

## Database Issues

### Database Connection Problems

**Problem**: Django cannot connect to the database.

**Symptoms**:
```
django.db.utils.OperationalError: could not connect to server
psycopg2.OperationalError: FATAL: password authentication failed
```

**Solutions**:

1. **Check Database Settings**:
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'musiccharts_db',
        'USER': 'musiccharts_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

2. **Test Database Connection**:
```bash
python manage.py dbshell
psql -h localhost -U musiccharts_user -d musiccharts_db
```

3. **Check PostgreSQL Status**:
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Migration Issues

**Problem**: Database migrations fail or are inconsistent.

**Solutions**:

1. **Check Migration Status**:
```bash
python manage.py showmigrations
```

2. **Create New Migrations**:
```bash
python manage.py makemigrations
python manage.py makemigrations app_name
```

3. **Apply Migrations**:
```bash
python manage.py migrate
python manage.py migrate app_name
```

4. **Reset Migrations (Development Only)**:
```bash
# WARNING: This will delete all data
python manage.py migrate app_name zero
python manage.py makemigrations app_name
python manage.py migrate app_name
```

## Celery Issues

### Service Architecture Overview

**Important**: MusicChartsAI requires **3 separate services** to run properly:

1. **Gunicorn** - Web server (handles HTTP requests)
2. **Celery Worker** - Background task processor  
3. **Celery Beat** - Task scheduler

**❌ What NOT to Do**: DO NOT add Celery to the Gunicorn configuration file. They are completely separate services.

### Celery Worker Not Starting

**Problem**: Celery workers fail to start or process tasks.

**Symptoms**:
```
ModuleNotFoundError: No module named 'apps.acrcloud'
celery.exceptions.NotRegistered: 'apps.soundcharts.tasks.sync_chart_rankings_task'
```

**Solutions**:

1. **Check Celery Configuration**:
```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

2. **Install Redis**:
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

3. **Test Redis Connection**:
```bash
redis-cli ping
# Should return: PONG
```

4. **Start Celery Worker**:
```bash
celery -A config worker -l info
```

### Service Management

**Option 1: Manual Commands (For Testing)**

**Terminal 1 - Gunicorn:**
```bash
cd /path/to/your/app
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
```

**Terminal 2 - Celery Worker:**
```bash
cd /path/to/your/app
celery -A config worker --loglevel=info
```

**Terminal 3 - Celery Beat:**
```bash
cd /path/to/your/app
celery -A config beat --loglevel=info
```

**Option 2: Background Processes**
```bash
cd /path/to/your/app

# Start all services in background
gunicorn --config gunicorn-simple.conf.py config.wsgi:application > logs/gunicorn.log 2>&1 &
celery -A config worker --loglevel=info > logs/celery-worker.log 2>&1 &
celery -A config beat --loglevel=info > logs/celery-beat.log 2>&1 &

# Check if they're running
ps aux | grep -E "(gunicorn|celery)"
```

**Option 3: Production with Systemd**
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

### Service Monitoring

**Check Service Status**:
```bash
# Check all processes
ps aux | grep -E "(gunicorn|celery)"

# Check specific service
pgrep -f "gunicorn.*config.wsgi"
pgrep -f "celery.*worker"
pgrep -f "celery.*beat"
```

**View Logs**:
```bash
# View log files directly
tail -f logs/gunicorn.log
tail -f logs/celery-worker.log
tail -f logs/celery-beat.log

# Or with systemd
sudo journalctl -u musiccharts-gunicorn -f
sudo journalctl -u musiccharts-celery -f
sudo journalctl -u musiccharts-celerybeat -f
```

**Test Celery Connection**:
```bash
# Test Redis connection
redis-cli ping

# Test Celery worker
celery -A config inspect active

# Test Celery beat
celery -A config inspect scheduled
```

### Task Queue Issues

**Problem**: Tasks are not being processed or are stuck in the queue.

**Solutions**:

1. **Check Celery Status**:
```bash
celery -A config inspect active
celery -A config inspect scheduled
celery -A config inspect stats
```

2. **Purge Task Queue**:
```bash
celery -A config purge
```

3. **Monitor Task Execution**:
```bash
celery -A config events
```

## API Integration Issues

### ACRCloud API Problems

**Problem**: ACRCloud API calls fail or return errors.

**Symptoms**:
```
401 Unauthorized
403 Forbidden
API quota exceeded
```

**Solutions**:

1. **Check API Credentials**:
```python
# Verify credentials in Django admin
# Go to /admin/acrcloud/acrcloudconfig/
```

2. **Test API Connection**:
```bash
python manage.py shell
>>> from apps.acrcloud.service import ACRCloudService
>>> service = ACRCloudService()
>>> # Test API call
```

3. **Check API Quotas**:
- Log into ACRCloud console
- Check usage and quotas
- Upgrade plan if needed

### SoundCharts API Issues

**Problem**: SoundCharts API integration fails.

**Solutions**:

1. **Verify API Keys**:
```python
# Check in Django settings
SOUNDCHARTS_APP_ID = 'your_app_id'
SOUNDCHARTS_API_KEY = 'your_api_key'
```

2. **Test API Endpoints**:
```bash
curl -H "Authorization: Bearer your_token" \
     "https://api.soundcharts.com/api/v2/track/..."
```

## Frontend Issues

### DataTables Not Loading

**Problem**: DataTables component fails to load or display data.

**Solutions**:

1. **Check JavaScript Console**:
```bash
# Open browser developer tools
# Check for JavaScript errors
```

2. **Verify API Endpoints**:
```bash
# Test API endpoints
curl http://localhost:8000/api/product/
```

3. **Check DataTables Configuration**:
```javascript
// Ensure jQuery and DataTables are loaded
// Check data format matches expected structure
```

### Flowbite Components Not Working

**Problem**: Flowbite components (modals, dropdowns, etc.) not functioning.

**Solutions**:

1. **Include Flowbite JavaScript**:
```html
<script src="https://unpkg.com/flowbite@1.8.1/dist/flowbite.min.js"></script>
```

2. **Check Component HTML**:
```html
<!-- Ensure proper data attributes -->
<button data-modal-target="modal" data-modal-toggle="modal">
```

3. **Initialize Components**:
```javascript
// Initialize Flowbite components
import 'flowbite/dist/flowbite.js';
```

## Performance Issues

### Slow Database Queries

**Problem**: Application is slow due to inefficient database queries.

**Solutions**:

1. **Enable Django Debug Toolbar**:
```python
# settings.py (development only)
INSTALLED_APPS = [
    'debug_toolbar',
]
```

2. **Optimize Queries**:
```python
# Use select_related and prefetch_related
queryset = Model.objects.select_related('foreign_key').prefetch_related('many_to_many')
```

3. **Add Database Indexes**:
```python
# models.py
class Meta:
    indexes = [
        models.Index(fields=['field1', 'field2']),
    ]
```

### Memory Issues

**Problem**: Application consumes too much memory.

**Solutions**:

1. **Monitor Memory Usage**:
```bash
# Check process memory usage
ps aux | grep python
htop
```

2. **Optimize Celery Workers**:
```python
# settings.py
CELERY_WORKER_CONCURRENCY = 2
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
```

3. **Implement Caching**:
```python
# Use Redis caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## Security Issues

### CSRF Token Errors

**Problem**: CSRF token validation fails.

**Solutions**:

1. **Include CSRF Token in Forms**:
```html
{% csrf_token %}
```

2. **Configure CSRF Settings**:
```python
# settings.py
CSRF_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_HTTPONLY = True
```

### SSL/HTTPS Issues

**Problem**: SSL certificate problems or mixed content warnings.

**Solutions**:

1. **Check SSL Configuration**:
```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443
```

2. **Configure Secure Settings**:
```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Monitoring and Debugging

### Log Analysis

**Enable Comprehensive Logging**:
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Health Checks

**Implement Health Check Endpoint**:
```python
# views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=503)
```

## Production Troubleshooting

### Deployment Issues

**Problem**: Application fails to deploy or start in production.

**Solutions**:

1. **Check Environment Variables**:
```bash
# Verify all required environment variables are set
echo $DATABASE_URL
echo $SECRET_KEY
echo $DEBUG
```

2. **Check File Permissions**:
```bash
# Ensure proper ownership
sudo chown -R www-data:www-data /path/to/app
sudo chmod -R 755 /path/to/app
```

3. **Check Service Status**:
```bash
# Check all services
sudo systemctl status gunicorn
sudo systemctl status celery
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Performance Monitoring

**Set Up Monitoring**:
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor system resources
htop
iotop
nethogs
```

## Getting Help

### Debug Information to Collect

When reporting issues, include:

1. **Error Messages**: Complete error messages and stack traces
2. **Environment**: OS, Python version, Django version
3. **Configuration**: Relevant settings.py configurations
4. **Logs**: Application and system logs
5. **Steps to Reproduce**: Detailed steps to reproduce the issue

### Useful Commands

```bash
# Check Django configuration
python manage.py check --deploy

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

### Support Channels

1. **Documentation**: Check this troubleshooting guide first
2. **GitHub Issues**: Report bugs and feature requests
3. **Community Forums**: Ask questions and get help
4. **Professional Support**: Contact for commercial support

## Conclusion

This troubleshooting guide covers the most common issues you may encounter with MusicChartsAI. For issues not covered here, check the logs, enable debug mode, and gather as much information as possible before seeking additional help.

Remember to always test solutions in a development environment before applying them to production systems.
