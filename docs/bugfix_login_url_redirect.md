# Bug Fix: Incorrect Login URL Redirect

**Date**: October 20, 2025  
**Status**: ✅ Fixed

---

## 🐛 **Problem**

When users tried to access protected pages without authentication, Django was redirecting them to `/accounts/login` instead of the correct custom login page at `/users/signin`.

---

## 🔍 **Root Cause**

**Missing `LOGIN_URL` setting in `config/settings.py`**

Django's default `LOGIN_URL` is `/accounts/login/`, which was being used because no custom value was configured.

The `@login_required` decorator and authentication middleware use this setting to determine where to redirect unauthenticated users.

---

## ✅ **Solution**

**File**: `config/settings.py`

**Added** (lines 247-249):
```python
LOGIN_URL = "/users/signin"  # Redirect unauthenticated users here
LOGIN_REDIRECT_URL = "/"  # Redirect after successful login
LOGOUT_REDIRECT_URL = "/users/signin"  # Optional: redirect after logout
```

---

## 📝 **Settings Explained**

| Setting | Value | Purpose |
|---------|-------|---------|
| `LOGIN_URL` | `/users/signin` | Where to redirect **unauthenticated** users |
| `LOGIN_REDIRECT_URL` | `/` | Where to redirect **after successful** login |
| `LOGOUT_REDIRECT_URL` | `/users/signin` | Where to redirect **after** logout |

---

## 🔧 **How It Works**

### **Before Fix** ❌

```
User tries to access protected page
    ↓
@login_required decorator checks authentication
    ↓
User not authenticated
    ↓
Django uses default LOGIN_URL = "/accounts/login"
    ↓
Redirect to /accounts/login (404 - doesn't exist!)
```

### **After Fix** ✅

```
User tries to access protected page
    ↓
@login_required decorator checks authentication
    ↓
User not authenticated
    ↓
Django uses custom LOGIN_URL = "/users/signin"
    ↓
Redirect to /users/signin (exists, shows login form)
```

---

## 🎯 **Affected Components**

All views using `@login_required` decorator now correctly redirect to `/users/signin`:

**Examples**:
- `apps/soundcharts/views.py`: All analytics views
  ```python
  @login_required
  def analytics_search_form(request):
      # ...
  ```

- `apps/pages/views.py`: Protected pages
- Any custom view with authentication requirements

---

## 🧪 **Testing**

### **Test Steps**

1. **Log out** (if logged in)
2. Try to access a protected page directly:
   - `/soundcharts/analytics/`
   - `/soundcharts/artists/`
   - Any page with `@login_required`
3. **Expected**: Redirect to `/users/signin`
4. **Before fix**: Redirected to `/accounts/login` (404)

### **Verification**

```bash
# Log out first
# Then try accessing protected page
curl -I http://localhost:8000/soundcharts/analytics/

# Expected response:
# HTTP/1.1 302 Found
# Location: /users/signin?next=/soundcharts/analytics/
```

---

## 📚 **Related Django Documentation**

**Django Settings Reference**:
- [`LOGIN_URL`](https://docs.djangoproject.com/en/4.2/ref/settings/#login-url)
- [`LOGIN_REDIRECT_URL`](https://docs.djangoproject.com/en/4.2/ref/settings/#login-redirect-url)
- [`LOGOUT_REDIRECT_URL`](https://docs.djangoproject.com/en/4.2/ref/settings/#logout-redirect-url)

**Django Authentication**:
- [`@login_required` decorator](https://docs.djangoproject.com/en/4.2/topics/auth/default/#the-login-required-decorator)

---

## 🔗 **URL Mapping**

**Authentication URLs** (from `apps/users/urls.py`):

| URL Pattern | View | Name | Purpose |
|-------------|------|------|---------|
| `/users/signin/` | `SignInView` | `signin` | Login page |
| `/users/signup/` | `SignUpView` | `signup` | Registration |
| `/users/signout/` | `signout_view` | `signout` | Logout |
| `/users/profile/` | `profile` | `profile` | User profile |

**Main URL Configuration** (from `config/urls.py`):
```python
path("users/", include("apps.users.urls")),
```

---

## ⚙️ **Configuration Details**

### **Where Settings Are Used**

1. **`@login_required` decorator**:
   ```python
   from django.contrib.auth.decorators import login_required
   
   @login_required  # Uses LOGIN_URL setting
   def my_protected_view(request):
       # ...
   ```

2. **Authentication middleware**:
   - `django.contrib.auth.middleware.AuthenticationMiddleware`
   - Checks if user is authenticated
   - Redirects to `LOGIN_URL` if not

3. **Login views**:
   - After successful login, redirect to `LOGIN_REDIRECT_URL`
   - Preserves `?next=` parameter for return to intended page

4. **Logout views**:
   - After logout, redirect to `LOGOUT_REDIRECT_URL`

---

## 💡 **Best Practices**

### **Always Set Custom LOGIN_URL**

If your project uses custom authentication URLs (not Django's default `/accounts/login/`), **always configure** `LOGIN_URL`:

```python
# settings.py
LOGIN_URL = "/your-custom-login-url"
```

### **Use Named URLs** (Alternative)

You can also use named URL patterns:

```python
# settings.py
LOGIN_URL = "signin"  # URL name from urls.py
```

But absolute paths are more explicit and less prone to errors.

### **Consistent Naming**

Keep authentication URL naming consistent:
- `/users/signin` ✅ (clear, explicit)
- `/accounts/login` ✅ (Django default convention)
- `/login` ✅ (simple, common)
- Mix of different styles ❌ (confusing)

---

## 🚀 **No Server Restart Needed**

Django loads settings once at startup, so you need to **restart the development server** for changes to take effect:

```bash
# Stop server (Ctrl+C)
# Then restart
python manage.py runserver
```

Or if using a production server (e.g., gunicorn):
```bash
# Reload workers
sudo systemctl reload your-app-name
```

---

## ✅ **Verification Checklist**

After fix:
- [x] `LOGIN_URL` set to `/users/signin`
- [x] `LOGIN_REDIRECT_URL` set to `/`
- [x] `LOGOUT_REDIRECT_URL` set to `/users/signin`
- [x] Server restarted
- [x] Tested: Accessing protected page redirects to `/users/signin`
- [x] Tested: Login redirects back to intended page (via `?next=` parameter)
- [x] Tested: Logout redirects to signin page

---

## 📊 **Impact**

**Affected**: All views using `@login_required`  
**Severity**: High (blocking user access)  
**Complexity**: Low (1-line fix)  
**Risk**: None (settings change only)

---

## 🎯 **Summary**

**Issue**: Django redirecting to non-existent `/accounts/login`  
**Cause**: Missing `LOGIN_URL` setting (using Django default)  
**Fix**: Added `LOGIN_URL = "/users/signin"` to `config/settings.py`  
**Result**: Correct redirect to custom login page ✅

---

**Last Updated**: October 20, 2025  
**Status**: 🟢 Fixed and Verified

