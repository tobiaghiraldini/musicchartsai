# ACRCloud Authentication Fix Guide

## 🚨 **Current Issue: 403 Authentication Exception**

Your ACRCloud configuration is correct, but the **Bearer Token** is invalid or doesn't have the right permissions.

## 🔧 **How to Fix the Authentication Issue**

### **Step 1: Get the Correct Bearer Token**

#### **1.1 Login to ACRCloud Console**
1. Go to [ACRCloud Console](https://console.acrcloud.com/)
2. Login with your account

#### **1.2 Navigate to API Keys**
1. Go to **Settings** → **API Keys** (or **Developer** → **API Keys`)
2. Look for **Console API** or **File Scanning API** keys
3. **NOT** the Identification API keys

#### **1.3 Generate New Token (if needed)**
1. If you don't have a Console API token, create one
2. Make sure it has **File Scanning** permissions
3. Copy the **Bearer Token** (starts with `eyJ...`)

### **Step 2: Update Your Configuration**

#### **2.1 Update Database Configuration**
```python
# In Django Admin: /admin/acrcloud/acrcloudconfig/
# Update the "MusicChartsAI" configuration:

{
    "name": "MusicChartsAI",
    "base_url": "https://api-eu-west-1.acrcloud.com",  # Keep this
    "bearer_token": "NEW_BEARER_TOKEN_HERE",  # ← Update this
    "container_id": "27492",  # Keep this
    "identify_host": "identify-eu-west-1.acrcloud.com",  # Keep this
    "identify_access_key": "5c7d668ccc...",  # Keep this
    "identify_access_secret": "your_secret_here",  # Keep this
    "is_active": True
}
```

#### **2.2 Update Environment Variables**
```bash
# In your .env file
ACRCLOUD_BEARER_TOKEN=NEW_BEARER_TOKEN_HERE
```

### **Step 3: Verify the Fix**

#### **3.1 Test Authentication**
```bash
# Run this to test the new token
source venv/bin/activate && python manage.py shell -c "
from apps.acrcloud.service import ACRCloudService
import urllib.request
import json

try:
    service = ACRCloudService()
    url = f'{service.config.base_url}/api/fs-containers'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {service.config.bearer_token}',
        'Accept': 'application/json'
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        response_data = json.loads(resp.read().decode('utf-8'))
        print('✅ Authentication successful!')
        print(f'Response: {response_data}')
except Exception as e:
    print(f'❌ Error: {str(e)}')
"
```

#### **3.2 Test File Upload**
```bash
# Test a complete file upload
source venv/bin/activate && python manage.py shell -c "
from apps.acrcloud.models import Song
from django.core.files.base import ContentFile
from apps.acrcloud.tasks import analyze_song_task

# Create a test song
song = Song()
song.user_id = 1  # Use your user ID
song.title = 'Test Song'
song.artist = 'Test Artist'
song.original_filename = 'test.mp3'
song.file_size = 1024
song.audio_file.save('test.mp3', ContentFile(b'fake audio data'))
song.save()

# Start analysis
analyze_song_task.delay(str(song.id))
print(f'Analysis started for song: {song.id}')
"
```

## 🔍 **Understanding ACRCloud Token Types**

### **Console API Token (What you need)**
- **Purpose**: File Scanning, container management, webhook configuration
- **Permissions**: Upload files, manage containers, receive webhooks
- **Format**: `eyJ0eXAiOiJKV1QiLCJh...` (JWT token)
- **Where to find**: Console → Settings → API Keys → Console API

### **Identification API Credentials (What you have)**
- **Purpose**: Audio identification, fingerprint matching
- **Permissions**: Identify audio, get recognition results
- **Format**: Access Key + Access Secret
- **Where to find**: Console → Settings → API Keys → Identification API

## 🌐 **Webhook Configuration for Localhost**

### **Option A: Use ngrok (Recommended)**
```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start ngrok tunnel
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io
# Use this for webhook: https://abc123.ngrok.io/acrcloud/webhook/file-scanning/
```

### **Option B: Use Mock Service (Development)**
```python
# In your Django settings
ACRCLOUD_USE_MOCK = True  # This will use mock_service.py instead of real API
```

## 📁 **Complete File Flow Explanation**

### **1. File Upload Process**
```
User uploads file via FilePond
    ↓
File saved to Django media/temp/
    ↓
Song record created in database
    ↓
Celery task: analyze_song_task triggered
```

### **2. ACRCloud Processing**
```
analyze_song_task
    ↓
ACRCloudService.analyze_song()
    ↓
File uploaded to ACRCloud File Scanning API
    ↓
File stored in ACRCloud cloud storage
    ↓
ACRCloud processes file asynchronously
    ↓
ACRCloud calls your webhook when complete
```

### **3. Webhook Processing**
```
ACRCloud webhook → /acrcloud/webhook/file-scanning/
    ↓
ACRCloudWebhookView receives callback
    ↓
process_acrcloud_webhook_task queued
    ↓
Task retrieves results from ACRCloud
    ↓
AnalysisReport created with fraud detection results
```

### **Key Points:**
- ✅ **Files ARE uploaded to ACRCloud** - They're stored in ACRCloud's cloud storage
- ✅ **Processing is asynchronous** - ACRCloud processes files in their cloud
- ✅ **Webhooks provide real-time updates** - No polling required
- ✅ **Results are retrieved via API** - Complete analysis data fetched

## 🚀 **Next Steps After Fixing Authentication**

### **1. Test Complete Flow**
```bash
# 1. Start Redis
redis-server --port 6379 --daemonize yes

# 2. Start Celery
celery -A config worker --loglevel=info

# 3. Start Django
python manage.py runserver

# 4. Test file upload via web interface
# Go to: http://localhost:8000/acrcloud/upload/
```

### **2. Monitor Progress**
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

### **3. Check Webhook Logs**
```bash
# View webhook calls
python manage.py shell -c "
from apps.acrcloud.models import WebhookLog
webhooks = WebhookLog.objects.all()[:5]
for webhook in webhooks:
    print(f'{webhook.created_at}: {webhook.file_id} - {webhook.status}')
"
```

## 🔒 **Security Notes**

### **1. Token Security**
- Store tokens in environment variables, not in code
- Rotate tokens regularly
- Use different tokens for development and production

### **2. Webhook Security**
- Use HTTPS for production webhooks
- Consider IP filtering for ACRCloud IP ranges
- Monitor webhook logs for suspicious activity

### **3. File Upload Security**
- Validate file types and sizes
- Scan uploaded files for malware
- Implement rate limiting

Once you fix the Bearer Token, your ACRCloud integration should work perfectly! 🚀
