# Content Security Policy (CSP) Troubleshooting Guide

## Issues Fixed

The CSP errors you're seeing are due to missing domains in the Content Security Policy. I've updated the Apache configuration to include:

### **Added Domains:**
- `https://unpkg.com` - For FilePond CSS and JS files
- `https://api.github.com` - For GitHub API connections

## Updated CSP Configuration

```apache
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://buttons.github.io https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; font-src 'self' data: https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.github.com;"
```

## Steps to Apply the Fix

### **1. Update Apache Configuration**
```bash
# Copy the updated config to your server
sudo cp apache-vhost.conf /etc/apache2/sites-available/musiccharts.conf

# Test Apache configuration
sudo apache2ctl configtest

# If test passes, restart Apache
sudo systemctl restart apache2
```

### **2. Clear Browser Cache**
```bash
# Clear browser cache or use incognito/private mode
# The CSP changes need to be reloaded
```

### **3. Test the Application**
1. Open browser developer tools (F12)
2. Go to Console tab
3. Reload the page
4. Check if CSP violations are resolved

## Alternative Approaches

### **Option 1: Temporarily Disable CSP (For Testing)**

If you want to test without CSP restrictions temporarily:

```apache
# Comment out the CSP header in Apache config
# Header always set Content-Security-Policy "..."
```

### **Option 2: More Permissive CSP (For Development)**

For development, you can use a more permissive CSP:

```apache
Header always set Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; font-src 'self' data: https:; img-src 'self' data: https:; connect-src 'self' https:;"
```

### **Option 3: Host External Resources Locally**

Instead of loading from external CDNs, download and host the resources locally:

```bash
# Download FilePond files
mkdir -p /home/users/ninjabit/musicchartsai/static/vendor/filepond
cd /home/users/ninjabit/musicchartsai/static/vendor/filepond

# Download CSS
wget https://unpkg.com/filepond/dist/filepond.min.css

# Download JS
wget https://unpkg.com/filepond/dist/filepond.min.js
wget https://unpkg.com/filepond-plugin-file-validate-type/dist/filepond-plugin-file-validate-type.min.js
wget https://unpkg.com/filepond-plugin-file-validate-size/dist/filepond-plugin-file-validate-size.min.js

# Update your Django templates to use local files
```

## CSP Directive Explanation

| Directive | Purpose | Current Setting |
|-----------|---------|-----------------|
| `default-src` | Default policy for all resources | `'self'` |
| `script-src` | JavaScript sources | `'self' 'unsafe-inline' 'unsafe-eval' https://buttons.github.io https://cdn.jsdelivr.net https://unpkg.com` |
| `style-src` | CSS stylesheet sources | `'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com` |
| `font-src` | Font sources | `'self' data: https://fonts.gstatic.com` |
| `img-src` | Image sources | `'self' data: https:` |
| `connect-src` | AJAX/fetch sources | `'self' https://api.github.com` |

## Common CSP Violations and Solutions

### **Violation: External Scripts**
```
Refused to load the script 'https://example.com/script.js'
```
**Solution**: Add `https://example.com` to `script-src`

### **Violation: External Stylesheets**
```
Refused to load the stylesheet 'https://example.com/style.css'
```
**Solution**: Add `https://example.com` to `style-src`

### **Violation: AJAX Requests**
```
Refused to connect to 'https://api.example.com'
```
**Solution**: Add `https://api.example.com` to `connect-src`

### **Violation: Inline Scripts**
```
Refused to execute inline script
```
**Solution**: Add `'unsafe-inline'` to `script-src` (already included)

## Testing CSP Configuration

### **1. Browser Developer Tools**
- Open F12 → Console tab
- Look for CSP violation messages
- Check Network tab for blocked requests

### **2. Online CSP Validator**
- Use online CSP validators to test your policy
- Example: https://csp-evaluator.withgoogle.com/

### **3. CSP Report-Only Mode**
For testing without blocking resources:

```apache
Header always set Content-Security-Policy-Report-Only "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://buttons.github.io https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; font-src 'self' data: https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.github.com;"
```

## Security Considerations

### **Balancing Security vs Functionality**

1. **Most Secure**: Host all resources locally
2. **Balanced**: Allow specific trusted domains
3. **Least Secure**: Use `'unsafe-inline'` and `'unsafe-eval'` (current setup)

### **Recommended Approach for Production**

1. **Audit External Resources**: Identify all external dependencies
2. **Host Locally**: Download and serve critical resources locally
3. **Whitelist Domains**: Only allow essential external domains
4. **Regular Updates**: Keep CSP policy updated as dependencies change

## Debugging Steps

### **1. Identify All External Resources**
```bash
# Search your templates for external resources
grep -r "https://" templates/
grep -r "http://" templates/

# Check for CDN usage
grep -r "unpkg\|cdnjs\|jsdelivr" templates/
```

### **2. Test Each Resource**
```bash
# Test if external resources are accessible
curl -I https://unpkg.com/filepond/dist/filepond.min.css
curl -I https://unpkg.com/filepond/dist/filepond.min.js
```

### **3. Monitor CSP Violations**
```bash
# Check Apache error logs for CSP-related issues
sudo tail -f /var/log/apache2/error.log | grep -i csp
```

## Expected Results After Fix

✅ **FilePond CSS loads without CSP violations**  
✅ **FilePond JS files load without CSP violations**  
✅ **GitHub API connections work**  
✅ **No CSP errors in browser console**  
✅ **File upload functionality works properly**

## If Issues Persist

1. **Check browser cache**: Clear cache or use incognito mode
2. **Verify Apache restart**: Ensure configuration was reloaded
3. **Check CSP syntax**: Ensure no syntax errors in the header
4. **Test with CSP disabled**: Temporarily comment out CSP header
5. **Use report-only mode**: Test without blocking resources

The updated CSP configuration should resolve all the FilePond and GitHub API CSP violations you're experiencing!
