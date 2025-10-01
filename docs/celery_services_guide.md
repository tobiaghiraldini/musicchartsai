# Celery Services Management Guide

## Overview

Your Music Charts AI application requires **3 separate services** to run properly:

1. **Gunicorn** - Web server (handles HTTP requests)
2. **Celery Worker** - Background task processor
3. **Celery Beat** - Task scheduler

## ❌ **What NOT to Do**

**DO NOT** add Celery to the Gunicorn configuration file. They are completely separate services.

## ✅ **Correct Service Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Apache/Nginx  │    │     Gunicorn     │    │  Celery Worker  │
│   (Port 80/443) │────│   (Port 8080)    │    │  (Background)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Django App     │    │  Celery Beat    │
                       │   (Web Logic)    │    │  (Scheduler)    │
                       └──────────────────┘    └─────────────────┘
```

## 🚀 **Running Services - Multiple Options**

### **Option 1: Using the Service Management Script (Recommended)**

I've created a script that makes it easy to manage all services:

```bash
# Make script executable (if not already done)
chmod +x scripts/start_services.sh

# Start all services
./scripts/start_services.sh start

# Check status
./scripts/start_services.sh status

# View logs
./scripts/start_services.sh logs

# Stop all services
./scripts/start_services.sh stop

# Restart all services
./scripts/start_services.sh restart
```

### **Option 2: Manual Commands (For Testing)**

**Terminal 1 - Gunicorn:**
```bash
cd /home/users/ninjabit/musicchartsai
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
```

**Terminal 2 - Celery Worker:**
```bash
cd /home/users/ninjabit/musicchartsai
celery -A config worker --loglevel=info
```

**Terminal 3 - Celery Beat:**
```bash
cd /home/users/ninjabit/musicchartsai
celery -A config beat --loglevel=info
```

### **Option 3: Background Processes**

```bash
cd /home/users/ninjabit/musicchartsai

# Start all services in background
gunicorn --config gunicorn-simple.conf.py config.wsgi:application > logs/gunicorn.log 2>&1 &
celery -A config worker --loglevel=info > logs/celery-worker.log 2>&1 &
celery -A config beat --loglevel=info > logs/celery-beat.log 2>&1 &

# Check if they're running
ps aux | grep -E "(gunicorn|celery)"
```

### **Option 4: Using Screen/Tmux (Development)**

```bash
# Install screen
sudo apt install screen

# Start screen session
screen -S musiccharts

# Run all services
gunicorn --config gunicorn-simple.conf.py config.wsgi:application &
celery -A config worker --loglevel=info &
celery -A config beat --loglevel=info &

# Detach: Ctrl+A, then D
# Reattach later: screen -r musiccharts
```

## 📋 **Service Commands Reference**

### **Gunicorn Commands**
```bash
# Start Gunicorn
gunicorn --config gunicorn-simple.conf.py config.wsgi:application

# Start with specific workers
gunicorn --workers=2 --bind=127.0.0.1:8080 config.wsgi:application

# Start in background
nohup gunicorn --config gunicorn-simple.conf.py config.wsgi:application &

# Stop Gunicorn
pkill -f "gunicorn.*config.wsgi"
```

### **Celery Worker Commands**
```bash
# Start worker
celery -A config worker --loglevel=info

# Start with specific concurrency
celery -A config worker --loglevel=info --concurrency=2

# Start in background
nohup celery -A config worker --loglevel=info > celery-worker.log 2>&1 &

# Stop worker
pkill -f "celery.*worker"
```

### **Celery Beat Commands**
```bash
# Start beat scheduler
celery -A config beat --loglevel=info

# Start in background
nohup celery -A config beat --loglevel=info > celery-beat.log 2>&1 &

# Stop beat
pkill -f "celery.*beat"
```

## 🔍 **Monitoring and Debugging**

### **Check Service Status**
```bash
# Check all processes
ps aux | grep -E "(gunicorn|celery)"

# Check specific service
pgrep -f "gunicorn.*config.wsgi"
pgrep -f "celery.*worker"
pgrep -f "celery.*beat"
```

### **View Logs**
```bash
# Using the service script
./scripts/start_services.sh logs gunicorn
./scripts/start_services.sh logs worker
./scripts/start_services.sh logs beat

# Or view log files directly
tail -f logs/gunicorn.log
tail -f logs/celery-worker.log
tail -f logs/celery-beat.log
```

### **Test Celery Connection**
```bash
# Test Redis connection
redis-cli ping

# Test Celery worker
celery -A config inspect active

# Test Celery beat
celery -A config inspect scheduled
```

## 🏭 **Production Setup with Systemd**

For production, use the systemd service files I created earlier:

### **1. Copy Service Files**
```bash
sudo cp systemd-services/*.service /etc/systemd/system/
```

### **2. Enable and Start Services**
```bash
# Enable services
sudo systemctl enable musiccharts-gunicorn
sudo systemctl enable musiccharts-celery
sudo systemctl enable musiccharts-celerybeat

# Start services
sudo systemctl start musiccharts-gunicorn
sudo systemctl start musiccharts-celery
sudo systemctl start musiccharts-celerybeat

# Check status
sudo systemctl status musiccharts-gunicorn
sudo systemctl status musiccharts-celery
sudo systemctl status musiccharts-celerybeat
```

### **3. Service Management**
```bash
# Start/Stop/Restart individual services
sudo systemctl start musiccharts-gunicorn
sudo systemctl stop musiccharts-celery
sudo systemctl restart musiccharts-celerybeat

# View logs
sudo journalctl -u musiccharts-gunicorn -f
sudo journalctl -u musiccharts-celery -f
sudo journalctl -u musiccharts-celerybeat -f
```

## 🐛 **Common Issues and Solutions**

### **Issue: Celery Worker Not Processing Tasks**
```bash
# Check Redis connection
redis-cli ping

# Check Celery configuration
python manage.py shell
>>> from celery import current_app
>>> current_app.conf.broker_url
>>> current_app.conf.result_backend
```

### **Issue: Celery Beat Not Scheduling Tasks**
```bash
# Check if beat is running
pgrep -f "celery.*beat"

# Check scheduled tasks
celery -A config inspect scheduled

# Clear beat schedule (if needed)
rm -f celerybeat-schedule*
```

### **Issue: Services Keep Dying**
```bash
# Check logs for errors
tail -f logs/gunicorn.log
tail -f logs/celery-worker.log
tail -f logs/celery-beat.log

# Check system resources
free -h
df -h
```

## 📊 **Performance Tuning**

### **Gunicorn Workers**
```bash
# Formula: (2 x CPU cores) + 1
# For 2 CPU cores: workers = 5
gunicorn --workers=5 --config gunicorn-simple.conf.py config.wsgi:application
```

### **Celery Worker Concurrency**
```bash
# Start with 2 worker processes
celery -A config worker --concurrency=2 --loglevel=info
```

### **Memory Usage**
```bash
# Monitor memory usage
htop
# or
ps aux --sort=-%mem | head -10
```

## 🚀 **Quick Start Commands**

### **For Development:**
```bash
# Use the service script
./scripts/start_services.sh start
```

### **For Testing:**
```bash
# Manual start in separate terminals
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
```

### **For Production:**
```bash
# Use systemd services
sudo systemctl start musiccharts-gunicorn
sudo systemctl start musiccharts-celery
sudo systemctl start musiccharts-celerybeat
```

## 📝 **Summary**

- **Gunicorn**: Handles web requests (HTTP server)
- **Celery Worker**: Processes background tasks
- **Celery Beat**: Schedules periodic tasks
- **All 3 services** must run simultaneously
- **Use the service script** for easy management
- **Use systemd** for production deployment

The key point is that these are **3 separate, independent services** that work together but are not part of each other's configuration!
