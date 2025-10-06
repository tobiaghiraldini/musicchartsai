# CI/CD Pipeline

## Overview

This guide covers setting up Continuous Integration and Continuous Deployment (CI/CD) pipelines for MusicChartsAI using Render, GitHub Actions, and other modern deployment platforms. These pipelines automate testing, building, and deploying your application to production environments.

## Render Deployment

### Overview

Render is a streamlined cloud hosting service that simplifies deployment and hosting experiences. MusicChartsAI includes pre-configured deployment scripts and blueprints for seamless Render deployment.

### Prerequisites

- Render account
- GitHub repository with your MusicChartsAI code
- Environment variables configured

### Deployment Process

#### 1. Connect Your Repository

1. **Create Render Account**: Sign up for a free Render account
2. **Connect GitHub**: Link your GitHub repository to Render
3. **Select Repository**: Choose your MusicChartsAI repository

#### 2. Configure Deployment Settings

Render uses the pre-configured `render.yaml` file to define deployment parameters:

```yaml
services:
  - type: web
    name: musiccharts-ai
    plan: starter
    env: python
    region: frankfurt  # Use same region as your database
    buildCommand: "./build.sh"
    startCommand: "gunicorn config.wsgi:application"
    envVars:
      - key: DEBUG
        value: False
      - key: SECRET_KEY
        generateValue: true
      - key: WEB_CONCURRENCY
        value: 4
      - key: DATABASE_URL
        fromDatabase:
          name: musiccharts-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: musiccharts-redis
          property: connectionString
```

#### 3. Environment Variables

Configure the following environment variables in Render:

**Required Variables:**
```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
REDIS_URL=your-redis-url
CELERY_BROKER_URL=your-redis-url
ALLOWED_HOSTS=your-render-app-url.onrender.com
```

**API Keys (Optional):**
```env
ACR_CLOUD_API_KEY=your-acr-cloud-key
ACR_CLOUD_API_SECRET=your-acr-cloud-secret
ACR_CLOUD_API_URL=your-acr-cloud-url
SOUNDCHARTS_APP_ID=your-soundcharts-app-id
SOUNDCHARTS_API_KEY=your-soundcharts-api-key
```

#### 4. Database Setup

Create a PostgreSQL database in Render:

1. Go to Render Dashboard
2. Click "New" → "PostgreSQL"
3. Configure database settings
4. Note the connection string

#### 5. Redis Setup

Create a Redis instance for caching and Celery:

1. Go to Render Dashboard
2. Click "New" → "Redis"
3. Configure Redis settings
4. Note the connection string

### Build Script Configuration

The `build.sh` script handles the deployment process:

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

# Install & Execute WebPack
npm i
npm run build

# Install Python modules
python -m pip install --upgrade pip
pip install -r requirements.txt

# Collect Static Files
python manage.py collectstatic --no-input

# Run Database Migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
# python manage.py createsuperuser --noinput
```

### Render Blueprint Specification

Extend your `render.yaml` for more advanced configurations:

```yaml
services:
  - type: web
    name: musiccharts-ai
    plan: starter
    env: python
    region: frankfurt
    buildCommand: "./build.sh"
    startCommand: "gunicorn config.wsgi:application"
    healthCheckPath: "/health/"
    autoDeploy: true
    envVars:
      - key: DEBUG
        value: False
      - key: SECRET_KEY
        generateValue: true
      - key: WEB_CONCURRENCY
        value: 4
      - key: DATABASE_URL
        fromDatabase:
          name: musiccharts-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: musiccharts-redis
          property: connectionString

databases:
  - name: musiccharts-db
    plan: starter
    region: frankfurt

  - name: musiccharts-redis
    type: redis
    plan: starter
    region: frankfurt
```

## GitHub Actions CI/CD

### Overview

GitHub Actions provides powerful CI/CD capabilities directly integrated with your repository. This setup includes automated testing, building, and deployment workflows.

### Workflow Configuration

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-django
    
    - name: Install Node.js dependencies
      run: |
        npm install
    
    - name: Build frontend assets
      run: |
        npm run build
    
    - name: Run Django checks
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        DEBUG: False
      run: |
        python manage.py check
        python manage.py makemigrations --check
        python manage.py collectstatic --noinput
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        DEBUG: False
      run: |
        python manage.py test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to Render
      uses: johnbeynon/render-deploy-action@v0.0.8
      with:
        service-id: ${{ secrets.RENDER_SERVICE_ID }}
        api-key: ${{ secrets.RENDER_API_KEY }}
        wait-for-success: true
```

### Environment Secrets

Configure the following secrets in your GitHub repository:

1. Go to Settings → Secrets and variables → Actions
2. Add the following secrets:

```
RENDER_SERVICE_ID=your-render-service-id
RENDER_API_KEY=your-render-api-key
```

### Advanced GitHub Actions Workflow

For more comprehensive CI/CD, use this enhanced workflow:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: '3.13'
  NODE_VERSION: '18'

jobs:
  lint-and-format:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 black isort
        pip install -r requirements.txt
    
    - name: Install Node.js dependencies
      run: npm install
    
    - name: Run Python linting
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check .
        isort --check-only .
    
    - name: Run JavaScript linting
      run: npm run lint

  test:
    runs-on: ubuntu-latest
    needs: lint-and-format
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-django pytest-cov
        npm install
    
    - name: Build frontend assets
      run: npm run build
    
    - name: Run Django checks
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        DEBUG: False
      run: |
        python manage.py check
        python manage.py makemigrations --check
        python manage.py collectstatic --noinput
    
    - name: Run tests with coverage
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        DEBUG: False
      run: |
        pytest --cov=. --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  security-scan:
    runs-on: ubuntu-latest
    needs: lint-and-format
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install security tools
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety
    
    - name: Run security scan
      run: |
        bandit -r . -f json -o bandit-report.json
        safety check --json --output safety-report.json
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json

  deploy-staging:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to Staging
      uses: johnbeynon/render-deploy-action@v0.0.8
      with:
        service-id: ${{ secrets.RENDER_STAGING_SERVICE_ID }}
        api-key: ${{ secrets.RENDER_API_KEY }}
        wait-for-success: true
    
    - name: Run staging tests
      run: |
        curl -f ${{ secrets.STAGING_URL }}/health/ || exit 1

  deploy-production:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to Production
      uses: johnbeynon/render-deploy-action@v0.0.8
      with:
        service-id: ${{ secrets.RENDER_SERVICE_ID }}
        api-key: ${{ secrets.RENDER_API_KEY }}
        wait-for-success: true
    
    - name: Run production health check
      run: |
        curl -f ${{ secrets.PRODUCTION_URL }}/health/ || exit 1
    
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Other Deployment Platforms

### Heroku Deployment

For Heroku deployment, create a `Procfile`:

```
web: gunicorn config.wsgi:application --log-file -
worker: celery -A config worker -l info
beat: celery -A config beat -l info
```

### Railway Deployment

Create `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn config.wsgi:application",
    "healthcheckPath": "/health/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### DigitalOcean App Platform

Create `.do/app.yaml`:

```yaml
name: musiccharts-ai
services:
- name: web
  source_dir: /
  github:
    repo: your-username/musiccharts-ai
    branch: main
  run_command: gunicorn config.wsgi:application
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  envs:
  - key: DEBUG
    value: "False"
  - key: SECRET_KEY
    value: ${SECRET_KEY}
databases:
- name: musiccharts-db
  engine: PG
  version: "15"
- name: musiccharts-redis
  engine: REDIS
  version: "7"
```

## Environment Management

### Environment-Specific Configurations

Create environment-specific settings files:

**`config/settings/staging.py`:**
```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['staging.yourdomain.com']

# Staging-specific database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'musiccharts_staging',
        'USER': 'staging_user',
        'PASSWORD': os.environ.get('STAGING_DB_PASSWORD'),
        'HOST': 'staging-db-host',
        'PORT': '5432',
    }
}

# Staging-specific Redis
REDIS_URL = os.environ.get('STAGING_REDIS_URL')
```

**`config/settings/production.py`:**
```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Production-specific settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Production database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'musiccharts_production',
        'USER': 'production_user',
        'PASSWORD': os.environ.get('PRODUCTION_DB_PASSWORD'),
        'HOST': 'production-db-host',
        'PORT': '5432',
    }
}

# Production Redis
REDIS_URL = os.environ.get('PRODUCTION_REDIS_URL')
```

## Monitoring and Alerting

### Health Checks

Implement health check endpoints:

```python
# apps/core/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """Comprehensive health check endpoint."""
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Redis check
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['services']['redis'] = 'healthy'
        else:
            health_status['services']['redis'] = 'unhealthy'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Celery check
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['services']['celery'] = 'healthy'
        else:
            health_status['services']['celery'] = 'unhealthy'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['services']['celery'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
```

### Deployment Notifications

Set up deployment notifications using Slack:

```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    channel: '#deployments'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
    fields: repo,message,commit,author,action,eventName,ref,workflow
```

## Best Practices

### Security

1. **Environment Variables**: Never commit secrets to version control
2. **Secret Management**: Use platform-specific secret management
3. **Access Control**: Implement proper access controls
4. **SSL/TLS**: Always use HTTPS in production
5. **Regular Updates**: Keep dependencies updated

### Performance

1. **Build Optimization**: Optimize build times and image sizes
2. **Caching**: Implement proper caching strategies
3. **Database Optimization**: Optimize database queries and indexes
4. **CDN**: Use CDN for static assets
5. **Monitoring**: Implement comprehensive monitoring

### Reliability

1. **Health Checks**: Implement comprehensive health checks
2. **Rollback Strategy**: Have rollback procedures in place
3. **Backup Strategy**: Implement regular backups
4. **Disaster Recovery**: Plan for disaster recovery scenarios
5. **Testing**: Comprehensive testing before deployment

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check build logs for specific errors
   - Verify all dependencies are correctly specified
   - Ensure environment variables are set

2. **Deployment Failures**
   - Check deployment logs
   - Verify service configurations
   - Test health check endpoints

3. **Environment Issues**
   - Verify environment variables
   - Check database connections
   - Validate external service integrations

### Debug Commands

```bash
# Check deployment status
curl -f https://your-app-url/health/

# View deployment logs
# (Platform-specific commands)

# Test database connection
python manage.py dbshell

# Test Redis connection
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'ok')
>>> cache.get('test')
```

## Conclusion

A well-configured CI/CD pipeline ensures reliable, automated deployments while maintaining code quality and security. Choose the deployment platform that best fits your needs and implement comprehensive monitoring and alerting to maintain system reliability.

For additional support, refer to the platform-specific documentation or contact the development team.
