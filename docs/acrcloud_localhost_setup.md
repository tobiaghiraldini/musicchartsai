# ACRCloud Localhost Development Setup

## 🚨 **Current Issues**

### **1. File Scanning API Authentication**
- **Error**: 403 Authentication Exception
- **Cause**: Bearer Token is not valid for File Scanning API
- **Solution**: Use mock service for development

### **2. Missing Webhook Configuration**
- **Issue**: ACRCloud can't reach localhost webhook
- **Solution**: Use ngrok or mock service

### **3. Analysis Report Missing**
- **Error**: `Analysis has no report`
- **Cause**: Analysis is failing due to API issues
- **Solution**: Fix configuration and use mock service

## 🔧 **Quick Fix for Localhost Development**

### **Option 1: Use Mock Service (Recommended for Development)**

#### **1.1 Enable Mock Service**
```python
# In your Django settings.py or .env file
ACRCLOUD_USE_MOCK = True
```

#### **1.2 Update Service to Use Mock**
```python
# In apps/acrcloud/service.py, modify the __init__ method
def __init__(self, config_name: str = None, use_mock: bool = None):
    if use_mock is None:
        use_mock = getattr(settings, 'ACRCLOUD_USE_MOCK', False)
    
    if use_mock:
        from .mock_service import MockACRCloudService
        self.mock_service = MockACRCloudService()
        self.config = None
    else:
        # ... existing code
```

#### **1.3 Update Tasks to Use Mock**
```python
# In apps/acrcloud/tasks.py, modify analyze_song_task
@shared_task
def analyze_song_task(song_id: str):
    try:
        song = Song.objects.get(id=song_id)
        
        # Check if we should use mock service
        use_mock = getattr(settings, 'ACRCLOUD_USE_MOCK', False)
        
        if use_mock:
            from .mock_service import MockACRCloudService
            service = MockACRCloudService()
        else:
            service = ACRCloudService()
        
        # ... rest of the code
```

### **Option 2: Use ngrok for Webhooks**

#### **2.1 Install and Start ngrok**
```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start ngrok tunnel
ngrok http 8000
```

#### **2.2 Update ACRCloud Configuration**
```python
# In Django Admin: /admin/acrcloud/acrcloudconfig/
# Update the webhook URL to use ngrok
# Example: https://abc123.ngrok.io/acrcloud/webhook/file-scanning/
```

#### **2.3 Update SITE_URL**
```bash
# In your .env file
SITE_URL=https://your-ngrok-url.ngrok.io
```

## 🚀 **Immediate Solution: Enable Mock Service**

Let me create a quick fix for you:

### **Step 1: Add Mock Service Setting**
```python
# In config/settings.py
ACRCLOUD_USE_MOCK = True  # Enable mock service for development
```

### **Step 2: Update Service to Handle Mock**
```python
# In apps/acrcloud/service.py
def __init__(self, config_name: str = None, use_mock: bool = None):
    if use_mock is None:
        use_mock = getattr(settings, 'ACRCLOUD_USE_MOCK', False)
    
    if use_mock:
        from .mock_service import MockACRCloudService
        self.mock_service = MockACRCloudService()
        self.config = None
        return
    
    # ... existing code for real service
```

### **Step 3: Update Tasks to Use Mock**
```python
# In apps/acrcloud/tasks.py
@shared_task
def analyze_song_task(song_id: str):
    try:
        song = Song.objects.get(id=song_id)
        
        # Check if we should use mock service
        use_mock = getattr(settings, 'ACRCLOUD_USE_MOCK', False)
        
        if use_mock:
            from .mock_service import MockACRCloudService
            service = MockACRCloudService()
        else:
            service = ACRCloudService()
        
        # ... rest of the code
```

## 🧪 **Test the Mock Service**

### **1. Test Mock Analysis**
```bash
# Run mock analysis
source venv/bin/activate && python manage.py shell -c "
from apps.acrcloud.models import Song
from apps.acrcloud.mock_service import MockACRCloudService
from django.core.files.base import ContentFile

# Create test song
song = Song()
song.user_id = 1
song.title = 'Mock Test Song'
song.artist = 'Mock Artist'
song.original_filename = 'mock_test.mp3'
song.file_size = 1024
song.audio_file.save('mock_test.mp3', ContentFile(b'fake audio data'))
song.save()

# Test mock service
service = MockACRCloudService()
result = service.analyze_song(song)
print(f'Mock analysis result: {result}')
"
```

### **2. Test Complete Flow**
```bash
# Test complete mock flow
source venv/bin/activate && python manage.py shell -c "
from apps.acrcloud.models import Song
from apps.acrcloud.tasks import analyze_song_task
from django.core.files.base import ContentFile

# Create test song
song = Song()
song.user_id = 1
song.title = 'Complete Test Song'
song.artist = 'Complete Artist'
song.original_filename = 'complete_test.mp3'
song.file_size = 1024
song.audio_file.save('complete_test.mp3', ContentFile(b'fake audio data'))
song.save()

# Start analysis
analyze_song_task.delay(str(song.id))
print(f'Analysis started for song: {song.id}')
"
```

## 📊 **Monitor Progress**

### **1. Check Analysis Status**
```bash
# Check analysis progress
source venv/bin/activate && python manage.py shell -c "
from apps.acrcloud.models import Song, Analysis, AnalysisReport
songs = Song.objects.all().order_by('-created_at')[:5]
for song in songs:
    print(f'{song.title}: {song.status}')
    analysis = song.analyses.first()
    if analysis:
        print(f'  Analysis: {analysis.status}')
        try:
            report = analysis.report
            print(f'  Report: {report.risk_level} - {report.match_type}')
        except:
            print('  Report: Not created yet')
"
```

### **2. Check Celery Logs**
```bash
# Monitor Celery worker logs
celery -A config worker --loglevel=info
```

## 🔄 **Production Setup (When Ready)**

### **1. Get Correct ACRCloud Credentials**
1. Go to [ACRCloud Console](https://console.acrcloud.com/)
2. Get **Console API** Bearer Token (not Identification API)
3. Update your ACRCloudConfig with correct credentials

### **2. Configure Webhook**
1. Set up ngrok or production domain
2. Configure webhook URL in ACRCloud Console
3. Update SITE_URL in environment

### **3. Disable Mock Service**
```python
# In config/settings.py
ACRCLOUD_USE_MOCK = False  # Use real ACRCloud API
```

## 🎯 **Next Steps**

1. **Enable mock service** for immediate development
2. **Test the complete flow** with mock data
3. **Get correct ACRCloud credentials** for production
4. **Set up ngrok** for webhook testing
5. **Switch to real API** when ready

This will get your ACRCloud integration working immediately for development! 🚀
