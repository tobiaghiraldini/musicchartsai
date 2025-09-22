# ACRCloud Setup Guide

## 🎯 **Overview**

This guide explains how to properly configure ACRCloud for your Django project, including localhost development setup and production deployment.

## 🔧 **Configuration Setup**

### **1. ACRCloud Console Setup**

#### **Step 1: Get Your Credentials**
1. Login to [ACRCloud Console](https://console.acrcloud.com/)
2. Go to **API Keys** section
3. Note down these values:
   - **Bearer Token** (for File Scanning API)
   - **Container ID** (for your File Scanning container)
   - **Identify Access Key** (for Identification API)
   - **Identify Access Secret** (for Identification API)

#### **Step 2: Configure Webhook (Production)**
1. Go to **File Scanning** → **Your Container** → **Settings**
2. Set **Result Callback URL**: `https://yourdomain.com/acrcloud/webhook/file-scanning/`
3. Enable webhook notifications

### **2. Django Configuration**

#### **Database Configuration (ACRCloudConfig Model)**
```python
# In Django Admin: /admin/acrcloud/acrcloudconfig/
{
    "name": "MusicChartsAI",
    "base_url": "https://api-eu-west-1.acrcloud.com",  # Your region
    "bearer_token": "eyJ0eXAiOiJKV1QiLCJh...",  # From ACRCloud Console
    "container_id": "27492",  # Your container ID
    "identify_host": "identify-eu-west-1.acrcloud.com",  # Your region
    "identify_access_key": "5c7d668ccc...",  # From ACRCloud Console
    "identify_access_secret": "your_secret_here",  # From ACRCloud Console
    "is_active": True
}
```

#### **Environment Variables (.env file)**
```bash
# ACRCloud Configuration
ACRCLOUD_BASE_URL=https://api-eu-west-1.acrcloud.com
ACRCLOUD_BEARER_TOKEN=eyJ0eXAiOiJKV1QiLCJh...
ACRCLOUD_CONTAINER_ID=27492
ACRCLOUD_IDENTIFY_HOST=identify-eu-west-1.acrcloud.com
ACRCLOUD_IDENTIFY_ACCESS_KEY=5c7d668ccc...
ACRCLOUD_IDENTIFY_ACCESS_SECRET=your_secret_here

# Site URL for webhooks
SITE_URL=http://localhost:8000  # For development
# SITE_URL=https://yourdomain.com  # For production
```

## 🌐 **Webhook Configuration**

### **For Localhost Development**

#### **Option A: Use ngrok (Recommended)**
```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start ngrok tunnel
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io
# Use this for webhook: https://abc123.ngrok.io/acrcloud/webhook/file-scanning/
```

#### **Option B: Use Mock Service (Development Only)**
For development without real ACRCloud calls:

```python
# In your Django settings or environment
ACRCLOUD_USE_MOCK = True  # Use mock service instead of real API
```

### **For Production**
```bash
# Set your production domain
export SITE_URL="https://yourdomain.com"

# Configure webhook in ACRCloud Console
# Result Callback URL: https://yourdomain.com/acrcloud/webhook/file-scanning/
```

## 📁 **File Flow Explanation**

### **Complete ACRCloud Processing Flow**

```
1. USER UPLOAD
   User uploads audio file via FilePond
   ↓
   File saved to Django media/temp/
   ↓
   Song record created in database
   ↓
   Celery task: analyze_song_task triggered

2. ACRCLOUD UPLOAD
   analyze_song_task calls ACRCloudService.analyze_song()
   ↓
   File uploaded to ACRCloud File Scanning API
   ↓
   File stored in ACRCloud cloud storage
   ↓
   ACRCloud processes file asynchronously

3. WEBHOOK PROCESSING
   ACRCloud calls your webhook when processing completes
   ↓
   ACRCloudWebhookView receives callback
   ↓
   process_acrcloud_webhook_task queued
   ↓
   Task retrieves results from ACRCloud
   ↓
   AnalysisReport created with fraud detection results

4. USER NOTIFICATION
   User sees updated status and analysis report
   ↓
   Email notification sent (if configured)
```

### **Key Points:**
- ✅ **Files ARE uploaded to ACRCloud** - They're stored in ACRCloud's cloud storage
- ✅ **Processing is asynchronous** - ACRCloud processes files in their cloud
- ✅ **Webhooks provide real-time updates** - No polling required
- ✅ **Results are retrieved via API** - Complete analysis data fetched

## 🐛 **Troubleshooting 403 Forbidden Error**

### **Common Causes:**

#### **1. Invalid Bearer Token**
```bash
# Check if token is valid
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api-eu-west-1.acrcloud.com/v1/containers/YOUR_CONTAINER_ID/files
```

#### **2. Wrong Container ID**
- Verify container ID in ACRCloud Console
- Check if container is active and has proper permissions

#### **3. Incorrect API Endpoint**
- Verify base URL matches your region
- Check if you're using the correct API version

#### **4. Missing Webhook Configuration**
- ACRCloud requires webhook URL for File Scanning
- Use ngrok for localhost development

### **Debug Steps:**

#### **1. Test API Connection**
```python
# Run this in Django shell
from apps.acrcloud.service import ACRCloudService
service = ACRCloudService()
# This will show detailed error information
```

#### **2. Check Webhook Endpoint**
```bash
# Test webhook endpoint
curl -X GET http://localhost:8000/acrcloud/webhook/file-scanning/
# Should return: {"status": "webhook_ready", "message": "ACRCloud webhook endpoint is active"}
```

#### **3. Monitor Celery Logs**
```bash
# Check Celery worker logs for detailed error messages
celery -A config worker --loglevel=debug
```

## 🚀 **Development vs Production**

### **Development Setup**
```bash
# Use ngrok for webhooks
ngrok http 8000

# Set environment
export SITE_URL="https://your-ngrok-url.ngrok.io"

# Start services
redis-server --port 6379 --daemonize yes
celery -A config worker --loglevel=info
python manage.py runserver
```

### **Production Setup**
```bash
# Set production domain
export SITE_URL="https://yourdomain.com"

# Configure webhook in ACRCloud Console
# Result Callback URL: https://yourdomain.com/acrcloud/webhook/file-scanning/

# Start services
redis-server --daemonize yes
celery -A config worker --loglevel=info --detach
gunicorn config.wsgi:application
```

## 📊 **Testing the Complete Flow**

### **1. Test File Upload**
```bash
# Upload a test file via web interface
# Go to: http://localhost:8000/acrcloud/upload/
```

### **2. Test Webhook (with ngrok)**
```bash
# Simulate ACRCloud webhook
curl -X POST -H "Content-Type: application/json" \
  -d '{"file_id":"test123","status":"completed"}' \
  https://your-ngrok-url.ngrok.io/acrcloud/webhook/file-scanning/
```

### **3. Monitor Analysis Progress**
```bash
# Check analysis status
python manage.py shell -c "
from apps.acrcloud.models import Song, Analysis
songs = Song.objects.all().order_by('-created_at')[:5]
for song in songs:
    print(f'{song.title}: {song.status}')
    analysis = song.analyses.first()
    if analysis:
        print(f'  Analysis: {analysis.status}')
"
```

## 🔒 **Security Considerations**

### **1. Webhook Security**
- Consider IP filtering for ACRCloud IP ranges
- Implement webhook signature validation
- Monitor webhook logs for suspicious activity

### **2. API Key Security**
- Store credentials in environment variables
- Use Django's secret key management
- Rotate API keys regularly

### **3. File Upload Security**
- Validate file types and sizes
- Scan uploaded files for malware
- Implement rate limiting

## 📈 **Monitoring and Debugging**

### **1. Webhook Logs**
```python
# Check webhook calls
from apps.acrcloud.models import WebhookLog
recent_webhooks = WebhookLog.objects.all()[:10]
for webhook in recent_webhooks:
    print(f"{webhook.created_at}: {webhook.file_id} - {webhook.status}")
```

### **2. Analysis Status**
```python
# Check analysis progress
from apps.acrcloud.models import Song, Analysis
processing_songs = Song.objects.filter(status='processing')
for song in processing_songs:
    print(f"Processing: {song.title}")
```

### **3. Error Tracking**
```python
# Check failed analyses
from apps.acrcloud.models import Song
failed_songs = Song.objects.filter(status='failed')
for song in failed_songs:
    print(f"Failed: {song.title}")
```

This setup will give you a complete, production-ready ACRCloud integration! 🚀
