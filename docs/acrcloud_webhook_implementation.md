# ACRCloud Webhook Implementation Guide

## 🎯 **Overview**

The ACRCloud integration now uses **proper webhook-based processing** instead of the naive `time.sleep()` approach. This provides real-time, asynchronous analysis that scales properly in production.

## 🔄 **New Webhook-Based Flow**

### **1. File Upload with Callback**
```python
# Upload file to ACRCloud with callback URL
file_id = service.upload_file_for_scanning(
    audio_file, 
    callback_url="https://yourdomain.com/acrcloud/webhook/file-scanning/"
)
```

### **2. Asynchronous Processing**
- ACRCloud processes the file in their cloud infrastructure
- No blocking waits or polling required
- Real-time processing status updates

### **3. Webhook Callback**
- ACRCloud calls your webhook when processing completes
- Webhook receives file_id, status, and processing results
- System automatically retrieves and processes results

### **4. Result Processing**
- Background Celery task processes webhook callback
- Retrieves complete analysis results from ACRCloud
- Updates database with fraud detection results
- Notifies user of completion

## 🛠️ **Implementation Details**

### **New Components Added**

#### **1. Webhook Endpoint** (`/acrcloud/webhook/file-scanning/`)
- **Purpose**: Receives ACRCloud processing completion callbacks
- **Security**: Logs all webhook calls with IP and payload
- **Processing**: Queues background task to retrieve results
- **Status Codes**: Returns appropriate HTTP responses

#### **2. Webhook Processing Task** (`process_acrcloud_webhook_task`)
- **Purpose**: Processes webhook callbacks in background
- **Actions**: Retrieves results, creates reports, updates status
- **Error Handling**: Handles failures and updates song status
- **Notifications**: Sends email notifications when configured

#### **3. Enhanced Upload Method** (`upload_file_for_scanning`)
- **Purpose**: Uploads files with callback URL parameter
- **Features**: Includes metadata and webhook configuration
- **Security**: Proper multipart form encoding
- **Logging**: Detailed upload tracking

#### **4. Webhook Logging** (`WebhookLog` model)
- **Purpose**: Logs all webhook calls for debugging and security
- **Data**: File ID, status, payload, source IP, timestamp
- **Admin**: Full admin interface for webhook monitoring
- **Security**: Tracks potential malicious webhook calls

## 📋 **Configuration Requirements**

### **1. ACRCloud Console Configuration**
In your ACRCloud File Scanning container settings:
```
Result Callback URL: https://yourdomain.com/acrcloud/webhook/file-scanning/
```

### **2. Django Settings**
```python
# Site URL for webhooks (required for callback URL generation)
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

# For production, set this to your actual domain:
# SITE_URL = 'https://yourdomain.com'
```

### **3. Environment Variables**
```bash
# For production
export SITE_URL="https://yourdomain.com"

# For local development
export SITE_URL="http://localhost:8000"
```

## 🧪 **Testing the Webhook Flow**

### **1. Test Webhook Endpoint**
```bash
# Health check
curl -X GET http://localhost:8000/acrcloud/webhook/file-scanning/

# Test webhook call
curl -X POST -H "Content-Type: application/json" \
  -d '{"file_id":"test123","status":"completed"}' \
  http://localhost:8000/acrcloud/webhook/file-scanning/
```

### **2. Check Webhook Logs**
- Navigate to `/admin/acrcloud/webhooklog/`
- View all incoming webhook calls
- Monitor for security issues or errors

### **3. Monitor Analysis Flow**
1. Upload a song via `/acrcloud/upload/`
2. Check song status changes: `uploaded` → `processing`
3. Monitor webhook logs for ACRCloud callbacks
4. Verify status update: `processing` → `analyzed`
5. View complete analysis report

## 🔒 **Security Considerations**

### **1. Webhook Validation**
- **IP Filtering**: Consider restricting to ACRCloud IP ranges
- **Request Validation**: Validate webhook payload structure
- **Rate Limiting**: Implement rate limiting for webhook endpoint
- **Authentication**: Consider webhook signature validation

### **2. Error Handling**
- **Malformed Requests**: Handle invalid webhook payloads
- **Missing Data**: Handle incomplete webhook data
- **Duplicate Calls**: Handle duplicate webhook notifications
- **Timeout Handling**: Handle webhook processing timeouts

### **3. Monitoring**
- **Webhook Logs**: All webhook calls are logged for security
- **Failed Processing**: Failed webhooks are logged with error details
- **Suspicious Activity**: Monitor for unusual webhook patterns

## 🚀 **Production Deployment**

### **1. Domain Configuration**
```bash
# Set your production domain
export SITE_URL="https://yourdomain.com"
```

### **2. ACRCloud Console Setup**
1. Login to ACRCloud Console
2. Navigate to your File Scanning container
3. Set **Result Callback URL**: `https://yourdomain.com/acrcloud/webhook/file-scanning/`
4. Enable webhook notifications

### **3. SSL Certificate**
- **Required**: ACRCloud requires HTTPS for production webhooks
- **Setup**: Ensure your domain has valid SSL certificate
- **Testing**: Test webhook endpoint with HTTPS

### **4. Firewall Configuration**
- **Webhook Endpoint**: Ensure `/acrcloud/webhook/file-scanning/` is accessible
- **Port Access**: Ensure port 443 (HTTPS) is open
- **IP Restrictions**: Consider restricting to ACRCloud IP ranges

## 📊 **Monitoring and Debugging**

### **1. Webhook Monitoring**
```python
# Check recent webhook calls
from apps.acrcloud.models import WebhookLog
recent_webhooks = WebhookLog.objects.all()[:10]
for webhook in recent_webhooks:
    print(f"{webhook.created_at}: {webhook.file_id} - {webhook.status}")
```

### **2. Analysis Status Tracking**
```python
# Check analysis progress
from apps.acrcloud.models import Song, Analysis
processing_songs = Song.objects.filter(status='processing')
for song in processing_songs:
    analysis = song.analyses.first()
    print(f"{song.title}: {analysis.acrcloud_file_id if analysis else 'No analysis'}")
```

### **3. Failed Analysis Investigation**
```python
# Check failed analyses
failed_songs = Song.objects.filter(status='failed')
for song in failed_songs:
    print(f"Failed: {song.title} - {song.updated_at}")
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Webhook Not Received**
- **Check**: ACRCloud console callback URL configuration
- **Verify**: SITE_URL setting is correct
- **Test**: Webhook endpoint accessibility from internet
- **Solution**: Ensure HTTPS and proper domain configuration

#### **2. Webhook Processing Fails**
- **Check**: Celery worker is running
- **Verify**: Database connections are working
- **Monitor**: Webhook logs for error details
- **Solution**: Check logs and fix underlying issues

#### **3. Analysis Stuck in Processing**
- **Check**: Webhook logs for missing callbacks
- **Verify**: ACRCloud file processing status
- **Monitor**: Analysis records for timeout
- **Solution**: Implement timeout handling and retry logic

### **4. File Upload Failures**
- **Check**: ACRCloud API credentials
- **Verify**: File format and size limits
- **Monitor**: Upload logs for errors
- **Solution**: Validate credentials and file requirements

## 🎯 **Benefits of Webhook Implementation**

### **1. Performance**
- ✅ **No Blocking**: No more `time.sleep()` blocking operations
- ✅ **Scalable**: Handles multiple concurrent analyses
- ✅ **Efficient**: Real-time processing without polling
- ✅ **Responsive**: UI remains responsive during processing

### **2. Reliability**
- ✅ **Asynchronous**: Processing doesn't depend on connection stability
- ✅ **Retry Logic**: Built-in retry mechanisms for failures
- ✅ **Error Handling**: Comprehensive error tracking and recovery
- ✅ **Monitoring**: Complete audit trail of all operations

### **3. Production Ready**
- ✅ **Webhook Security**: IP logging and payload validation
- ✅ **SSL Support**: HTTPS webhook endpoints
- ✅ **Monitoring**: Complete webhook and analysis monitoring
- ✅ **Maintenance**: Easy debugging and troubleshooting

## 📈 **Next Steps**

### **For Development Testing**
1. **Use Mock Analysis**: Test complete flow without ACRCloud API
2. **Webhook Testing**: Test webhook endpoint with curl commands
3. **UI Testing**: Verify dashboard updates and status changes

### **For Production Deployment**
1. **Configure ACRCloud**: Set callback URL in ACRCloud console
2. **SSL Setup**: Ensure HTTPS domain configuration
3. **Monitor Webhooks**: Set up webhook monitoring and alerting
4. **Performance Testing**: Test with real audio files and analysis

The webhook-based implementation is now **production-ready** and follows ACRCloud best practices for scalable, real-time audio analysis! 🚀
