# Static Files Troubleshooting Guide

## Issues Fixed in Your Configuration

### 1. Content Security Policy (CSP) Issues
**Problem**: CSP was blocking external resources like Google Fonts and GitHub buttons.

**Solution**: Updated CSP to allow:
- `https://fonts.googleapis.com` for stylesheets
- `https://fonts.gstatic.com` for fonts  
- `https://buttons.github.io` for GitHub buttons
- `https://cdn.jsdelivr.net` for CDN resources

### 2. Static File Path Issues
**Problem**: Inconsistent paths between Apache config and actual file locations.

**Solution**: Updated all paths to use `/home/users/ninjabit/musicchartsai/` consistently.

### 3. MIME Type Issues
**Problem**: Files being served as `text/html` instead of proper CSS/JS MIME types.

**Solution**: Added explicit MIME type declarations in Apache config.

### 4. Port Configuration
**Problem**: Gunicorn config was using port 8000, but you're running on 8080.

**Solution**: Updated Gunicorn config to use port 8080.

## Steps to Fix Your Deployment

### 1. Update Apache Configuration
```bash
# Copy the updated Apache config to your server
sudo cp apache-vhost.conf /etc/apache2/sites-available/musiccharts.conf

# Test Apache configuration
sudo apache2ctl configtest

# If test passes, restart Apache
sudo systemctl restart apache2
```

### 2. Check Static Files Location
```bash
# Verify static files exist
ls -la /home/users/ninjabit/musicchartsai/staticfiles/

# Check if staticfiles directory has proper structure
ls -la /home/users/ninjabit/musicchartsai/staticfiles/dist/
ls -la /home/users/ninjabit/musicchartsai/staticfiles/images/
```

### 3. Fix File Permissions
```bash
# Set proper ownership (replace 'youruser' with actual user)
sudo chown -R youruser:www-data /home/users/ninjabit/musicchartsai/staticfiles/
sudo chown -R youruser:www-data /home/users/ninjabit/musicchartsai/media/

# Set proper permissions
sudo chmod -R 755 /home/users/ninjabit/musicchartsai/staticfiles/
sudo chmod -R 755 /home/users/ninjabit/musicchartsai/media/

# Ensure Apache can read the files
sudo chmod -R 644 /home/users/ninjabit/musicchartsai/staticfiles/*
```

### 4. Recollect Static Files
```bash
# Navigate to your Django project
cd /home/users/ninjabit/musicchartsai

# Activate virtual environment (if using one)
source venv/bin/activate  # or however you activate your venv

# Collect static files again
python manage.py collectstatic --noinput --clear
```

### 5. Restart Services
```bash
# Restart Apache
sudo systemctl restart apache2

# Restart Gunicorn (if using systemd)
sudo systemctl restart musiccharts-gunicorn

# Or if running manually, stop and restart
# Kill existing Gunicorn process
pkill -f gunicorn

# Start Gunicorn with updated config
gunicorn --config gunicorn-prod.conf.py config.wsgi:application
```

## Verification Steps

### 1. Test Static Files Directly
```bash
# Test if static files are accessible
curl -I https://musicchartsai.ninjabit.com/static/dist/main.css
curl -I https://musicchartsai.ninjabit.com/static/images/logo.png
```

### 2. Check Apache Error Logs
```bash
# Monitor Apache error logs
sudo tail -f /var/log/apache2/error.log

# Check specific site error log
sudo tail -f /var/log/apache2/musiccharts_error.log
```

### 3. Test in Browser
1. Open browser developer tools (F12)
2. Go to Network tab
3. Reload the page
4. Check if static files load with 200 status codes
5. Verify no 403 or 404 errors for static files

## Common Issues and Solutions

### Issue: 403 Forbidden Errors
**Causes**:
- Wrong file permissions
- Apache can't access the directory
- SELinux restrictions (if enabled)

**Solutions**:
```bash
# Fix permissions
sudo chmod -R 755 /home/users/ninjabit/musicchartsai/staticfiles/
sudo chmod -R 644 /home/users/ninjabit/musicchartsai/staticfiles/*

# Check Apache user
ps aux | grep apache2

# Ensure Apache user can access files
sudo chown -R www-data:www-data /home/users/ninjabit/musicchartsai/staticfiles/
```

### Issue: MIME Type Errors
**Causes**:
- Apache not recognizing file types
- Missing MIME type configuration

**Solutions**:
```bash
# Check if mod_mime is enabled
sudo a2enmod mime

# Restart Apache
sudo systemctl restart apache2
```

### Issue: CSP Violations
**Causes**:
- Too restrictive Content Security Policy
- Missing external domains

**Solutions**:
- Update CSP in Apache config (already fixed)
- Temporarily disable CSP for testing:
```apache
# Comment out CSP header for testing
# Header always set Content-Security-Policy "..."
```

## Testing Commands

### Check Static Files Structure
```bash
# List static files
find /home/users/ninjabit/musicchartsai/staticfiles/ -type f | head -20

# Check file sizes
du -sh /home/users/ninjabit/musicchartsai/staticfiles/

# Verify specific files exist
ls -la /home/users/ninjabit/musicchartsai/staticfiles/dist/main.css
ls -la /home/users/ninjabit/musicchartsai/staticfiles/dist/main.bundle.js
```

### Test Apache Configuration
```bash
# Test configuration syntax
sudo apache2ctl configtest

# List enabled sites
sudo a2ensite -l

# Check loaded modules
sudo apache2ctl -M | grep -E "(mime|rewrite|proxy|headers)"
```

### Test File Access
```bash
# Test as Apache user
sudo -u www-data ls -la /home/users/ninjabit/musicchartsai/staticfiles/

# Test file reading
sudo -u www-data cat /home/users/ninjabit/musicchartsai/staticfiles/dist/main.css | head -5
```

## Expected Results After Fixes

1. **Static files load with 200 status codes**
2. **No CSP violations in browser console**
3. **CSS and JS files load with correct MIME types**
4. **Images and favicons load properly**
5. **External resources (fonts, scripts) load without CSP errors**

## If Issues Persist

1. **Check Django settings**:
```python
# In settings.py, verify:
STATIC_URL = '/static/'
STATIC_ROOT = '/home/users/ninjabit/musicchartsai/staticfiles/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
```

2. **Verify collectstatic output**:
```bash
python manage.py collectstatic --verbosity=2
```

3. **Test with minimal Apache config**:
```apache
<VirtualHost *:443>
    ServerName musicchartsai.ninjabit.com
    
    Alias /static/ /home/users/ninjabit/musicchartsai/staticfiles/
    <Directory /home/users/ninjabit/musicchartsai/staticfiles/>
        Require all granted
    </Directory>
    
    ProxyPass /static/ !
    ProxyPass / http://127.0.0.1:8080/
    ProxyPassReverse / http://127.0.0.1:8080/
</VirtualHost>
```

This should resolve all the static file issues you're experiencing!

