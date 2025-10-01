# Gunicorn Configuration Troubleshooting

## Issues with Production Configuration

The error you encountered with `gunicorn-prod.conf.py` is likely due to several configuration issues:

### **Problems Identified:**

1. **Log File Paths**: The original config tried to write to `/var/log/musiccharts/` which may not exist or be writable
2. **PID File Path**: The `/var/run/musiccharts-gunicorn.pid` path may not be writable
3. **User/Group Settings**: The `user = "musiccharts"` and `group = "musiccharts"` settings require root privileges
4. **Temporary Directory**: The `worker_tmp_dir = "/dev/shm"` may not be accessible

## Solutions

### **Option 1: Use the Simple Configuration (Recommended for Testing)**

```bash
# Use the simplified configuration
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
```

The `gunicorn-simple.conf.py` file I created:
- ✅ Logs to console (stdout/stderr) instead of files
- ✅ Removes problematic user/group settings
- ✅ Removes PID file requirements
- ✅ Uses safe temporary directory settings

### **Option 2: Fix the Production Configuration**

If you want to use the production config, you need to create the necessary directories and set permissions:

```bash
# Create log directory
sudo mkdir -p /var/log/musiccharts
sudo chown $USER:$USER /var/log/musiccharts
sudo chmod 755 /var/log/musiccharts

# Create PID directory (if needed)
sudo mkdir -p /var/run
sudo chown $USER:$USER /var/run

# Then use the production config
gunicorn --config gunicorn-prod.conf.py config.wsgi:application
```

### **Option 3: Use Command Line Arguments (Current Working Method)**

Your current working command:
```bash
gunicorn --workers=2 --bind=0.0.0.0:8080 config.wsgi:application
```

This is equivalent to:
```bash
gunicorn --workers=2 --bind=127.0.0.1:8080 config.wsgi:application
```

## Configuration Comparison

| Setting | Command Line | Simple Config | Production Config |
|---------|--------------|---------------|-------------------|
| Workers | 2 | 2 | CPU cores * 2 + 1 |
| Bind | 0.0.0.0:8080 | 127.0.0.1:8080 | 127.0.0.1:8080 |
| Logging | Default | Console | File-based |
| User/Group | Current user | Current user | musiccharts |
| PID File | No | No | Yes |

## Recommended Approach

### **For Development/Testing:**
```bash
# Use the simple configuration
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
```

### **For Production (when ready):**
1. Set up proper directories and permissions
2. Use the production configuration
3. Or use systemd service files (which handle permissions automatically)

## Testing the Configurations

### **Test Simple Config:**
```bash
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
```

### **Test with Verbose Output:**
```bash
gunicorn --config gunicorn-simple.conf.py --log-level debug config.wsgi:application
```

### **Test Production Config (after fixing permissions):**
```bash
# First create directories
sudo mkdir -p /var/log/musiccharts
sudo chown $USER:$USER /var/log/musiccharts

# Then test
gunicorn --config gunicorn-prod.conf.py config.wsgi:application
```

## Common Gunicorn Errors and Solutions

### **Error: Permission Denied**
```bash
# Solution: Run without user/group settings or use sudo
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
```

### **Error: Cannot Write PID File**
```bash
# Solution: Comment out pidfile in config or create directory
sudo mkdir -p /var/run
sudo chown $USER:$USER /var/run
```

### **Error: Cannot Write Log File**
```bash
# Solution: Use console logging or create log directory
sudo mkdir -p /var/log/musiccharts
sudo chown $USER:$USER /var/log/musiccharts
```

### **Error: Worker Process Died**
```bash
# Solution: Check Django settings and reduce workers
gunicorn --workers=1 --bind=127.0.0.1:8080 config.wsgi:application
```

## Debugging Steps

### **1. Test with Minimal Configuration:**
```bash
gunicorn --bind=127.0.0.1:8080 config.wsgi:application
```

### **2. Add Workers Gradually:**
```bash
gunicorn --workers=1 --bind=127.0.0.1:8080 config.wsgi:application
gunicorn --workers=2 --bind=127.0.0.1:8080 config.wsgi:application
```

### **3. Test Configuration File:**
```bash
# Check if config file is valid Python
python gunicorn-simple.conf.py

# Test with verbose logging
gunicorn --config gunicorn-simple.conf.py --log-level debug config.wsgi:application
```

### **4. Check Django Application:**
```bash
# Test Django directly
python manage.py runserver 127.0.0.1:8080

# Check Django settings
python manage.py check --deploy
```

## Production Recommendations

### **When Ready for Production:**

1. **Use systemd services** (handles permissions automatically)
2. **Set up proper log rotation**
3. **Configure monitoring**
4. **Use reverse proxy** (Apache/Nginx)

### **Systemd Service Example:**
```ini
[Unit]
Description=Music Charts AI Gunicorn
After=network.target

[Service]
Type=exec
User=youruser
Group=youruser
WorkingDirectory=/home/users/ninjabit/musicchartsai
Environment=PATH=/home/users/ninjabit/.pyenv/versions/musicchartsai/bin
ExecStart=/home/users/ninjabit/.pyenv/versions/musicchartsai/bin/gunicorn --config gunicorn-prod.conf.py config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

## Quick Fix for Your Current Issue

**Use this command for now:**
```bash
gunicorn --config gunicorn-simple.conf.py config.wsgi:application
```

This should work without any permission issues and give you the same functionality as your working command line version, but with a proper configuration file.
