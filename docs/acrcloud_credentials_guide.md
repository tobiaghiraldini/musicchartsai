# ACRCloud Credentials Guide - Fix 403 Forbidden Error

## 🚨 **Current Issue: 403 Forbidden Error**

Your **Bearer Token** is not valid for the **Console API** (File Scanning). You have **Project API credentials** but need **Console API credentials**.

## 🔍 **ACRCloud API Types Explained**

### **1. Project API (What you have)**
- **Purpose**: Audio identification, fingerprint matching
- **Credentials**: Access Key + Access Secret
- **APIs**: `/v1/identify`, `/v1/identify-by-file`
- **Status**: ✅ Working (your Identification API works)

### **2. Console API (What you need)**
- **Purpose**: File Scanning, container management, webhooks
- **Credentials**: Bearer Token (JWT)
- **APIs**: `/api/fs-containers/*`, `/api/fs-containers/{id}/files`
- **Status**: ❌ 403 Forbidden (your Bearer Token is invalid)

## 🔧 **How to Get Console API Credentials**

### **Step 1: Login to ACRCloud Console**
1. Go to [ACRCloud Console](https://console.acrcloud.com/)
2. Login with your account

### **Step 2: Navigate to API Keys**
1. Look for **"API Keys"** or **"Developer"** section
2. You should see two sections:
   - **Project API** (what you have)
   - **Console API** (what you need)

### **Step 3: Generate Console API Token**
1. In the **Console API** section, click **"Generate Token"** or **"Create API Key"**
2. Make sure it has **File Scanning** permissions
3. Copy the **Bearer Token** (starts with `eyJ...`)

### **Step 4: Update Your Configuration**
```python
# In Django Admin: /admin/acrcloud/acrcloudconfig/
# Update the "MusicChartsAI" configuration:

{
    "name": "MusicChartsAI",
    "base_url": "https://api-eu-west-1.acrcloud.com",  # Keep this
    "bearer_token": "NEW_CONSOLE_API_BEARER_TOKEN",  # ← Update this
    "container_id": "27492",  # Keep this
    "identify_host": "identify-eu-west-1.acrcloud.com",  # Keep this
    "identify_access_key": "ac2bc64f1a79e9f28d8063dace46a894",  # Keep this
    "identify_access_secret": "D34afusJ2l...",  # Keep this
    "is_active": True
}
```

## 🧪 **Test the Fix**

### **1. Test Console API Authentication**
```bash
source venv/bin/activate && python manage.py shell -c "
from apps.acrcloud.service import ACRCloudService
import urllib.request
import json

service = ACRCloudService()
url = f'{service.config.base_url}/api/fs-containers'
req = urllib.request.Request(url, headers={
    'Authorization': f'Bearer {service.config.bearer_token}',
    'Accept': 'application/json'
})

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        response = json.loads(resp.read().decode('utf-8'))
        print('✅ Console API: SUCCESS')
        print(f'Response: {response}')
except urllib.error.HTTPError as e:
    print(f'❌ Console API: HTTP {e.code} - {e.reason}')
    print(f'Response: {e.read().decode()}')
"
```

### **2. Test File Upload**
```bash
source venv/bin/activate && python manage.py shell -c "
from apps.acrcloud.models import Song
from apps.acrcloud.tasks import analyze_song_task
from django.core.files.base import ContentFile

# Create test song
song = Song()
song.user_id = 1
song.title = 'Real API Test'
song.artist = 'Real Artist'
song.original_filename = 'real_test.mp3'
song.file_size = 1024
song.audio_file.save('real_test.mp3', ContentFile(b'fake audio data'))
song.save()

# Start analysis
analyze_song_task.delay(str(song.id))
print(f'Analysis started for song: {song.id}')
"
```

## 🔄 **Alternative: Use Mock Service for Development**

If you want to continue development without real ACRCloud credentials:

### **1. Keep Mock Service Enabled**
```python
# In config/settings.py (already set)
ACRCLOUD_USE_MOCK = True
```

### **2. Test Mock Service**
```bash
# Mock service should work without real credentials
source venv/bin/activate && python manage.py shell -c "
from apps.acrcloud.service import ACRCloudService
from apps.acrcloud.models import Song
from django.core.files.base import ContentFile

# Create test song
song = Song()
song.user_id = 1
song.title = 'Mock Test'
song.artist = 'Mock Artist'
song.original_filename = 'mock_test.mp3'
song.file_size = 1024
song.audio_file.save('mock_test.mp3', ContentFile(b'fake audio data'))
song.save()

# Test mock analysis
service = ACRCloudService()
result = service.analyze_song(str(song.id))
print(f'Mock result: {result}')
"
```

## 📊 **ACRCloud Console Navigation Guide**

### **If you can't find Console API section:**

1. **Look for these terms:**
   - "API Keys"
   - "Developer"
   - "Console API"
   - "File Scanning API"
   - "Bearer Token"

2. **Check different sections:**
   - Settings → API Keys
   - Developer → API Keys
   - Account → API Keys
   - File Scanning → Settings

3. **Look for JWT tokens:**
   - Console API uses JWT tokens (start with `eyJ...`)
   - Project API uses Access Key + Secret

## 🚀 **Production Setup**

### **1. Get Console API Credentials**
- Generate Console API Bearer Token
- Ensure it has File Scanning permissions
- Update ACRCloudConfig in Django Admin

### **2. Configure Webhook**
```bash
# For localhost development
ngrok http 8000
# Use ngrok URL for webhook: https://abc123.ngrok.io/acrcloud/webhook/file-scanning/

# For production
# Set webhook URL in ACRCloud Console: https://yourdomain.com/acrcloud/webhook/file-scanning/
```

### **3. Disable Mock Service**
```python
# In config/settings.py
ACRCLOUD_USE_MOCK = False  # Use real ACRCloud API
```

## 🔍 **Debugging Steps**

### **1. Check Token Format**
```python
# Console API Bearer Token should look like:
# eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJhY3JjbG91ZCIsImV4cCI6MTY5...
# It's a JWT token, not a simple string
```

### **2. Check Permissions**
- Make sure the Console API token has **File Scanning** permissions
- Check if the token is not expired
- Verify the token is for the correct region (eu-west-1)

### **3. Check Container ID**
- Verify the container ID (27492) exists in your account
- Make sure the container is active and has proper permissions

## 🎯 **Quick Fix Summary**

1. **Get Console API Bearer Token** from ACRCloud Console
2. **Update ACRCloudConfig** with the new Bearer Token
3. **Test the API** to confirm 403 error is fixed
4. **Test file upload** to confirm complete flow works

The 403 error will be resolved once you get the correct Console API Bearer Token! 🚀
