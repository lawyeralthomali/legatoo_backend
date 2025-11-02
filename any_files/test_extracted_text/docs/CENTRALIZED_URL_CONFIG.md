# Centralized URL Configuration

This document explains the centralized URL configuration system implemented across the application.

## Overview

All URLs are now managed from a single point to ensure consistency and easy maintenance across:
- Backend Python services (`email_service.py`)
- Frontend HTML files (`email-verification.html`, `password-reset.html`, `login.html`)
- JavaScript configuration (`url-config.js`)

## Files Modified

### 1. Backend Configuration
- **File**: `legatoo_backend/app/config/urls.py`
- **Purpose**: Centralized URL configuration for Python backend services
- **Usage**: Import and use `get_url_config()` function

### 2. Frontend Configuration
- **File**: `legatoo_backend/url-config.js`
- **Purpose**: Centralized URL configuration for JavaScript frontend
- **Usage**: Access via `window.urlConfig` global object

### 3. Updated Files
- `legatoo_backend/app/services/email_service.py`
- `legatoo_backend/email-verification.html`
- `legatoo_backend/password-reset.html`
- `legatoo_backend/login.html`

## Configuration Structure

### Environment Variables
The system uses these environment variables for configuration:

```env
# Environment detection
ENVIRONMENT=development  # or production

# Base URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://127.0.0.1:8000

# Production URLs (override for production)
FRONTEND_URL=https://legatoo.westlinktowing.com
BACKEND_URL=https://api.legatoo.westlinktowing.com
```

### URL Categories

#### 1. Authentication URLs
- Login: `/auth/login`
- Signup: `/auth/signup`
- Forgot Password: `/auth/forgot-password`
- Email Verification: `/email-verification.html`
- Password Reset: `/password-reset.html`
- Dashboard: `/dashboard`

#### 2. API URLs
- Auth Base: `/api/v1/auth`
- Login: `/api/v1/auth/login`
- Signup: `/api/v1/auth/signup`
- Verify Email: `/api/v1/auth/verify-email`
- Forgot Password: `/api/v1/auth/forgot-password`
- Confirm Password Reset: `/api/v1/auth/confirm-password-reset`
- Refresh Token: `/api/v1/auth/refresh-token`
- Logout: `/api/v1/auth/logout`
- Profile: `/api/v1/profiles/me`
- Subscriptions: `/api/v1/subscriptions/status`
- Plans: `/api/v1/subscriptions/plans`
- Premium: `/api/v1/premium/status`
- Features: `/api/v1/premium/feature-limits`

## Usage Examples

### Backend Python Usage

```python
from app.config.urls import get_url_config

# Get configuration instance
url_config = get_url_config()

# Get specific URLs
verification_url = url_config.get_verification_url(token)
reset_url = url_config.get_password_reset_url(token)
api_url = url_config.get_api_url('login')
frontend_url = url_config.get_frontend_url('dashboard')
```

### Frontend JavaScript Usage

```javascript
// Access configuration
const config = window.urlConfig;

// Get specific URLs
const loginUrl = config.authUrls.login;
const apiUrl = config.apiUrls.login;
const verificationUrl = config.getVerificationUrl(token);

// Use in fetch requests
fetch(config.apiUrls.login, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
});
```

## Environment Detection

### Development Environment
- Hostname: `localhost` or `127.0.0.1`
- Frontend URL: `http://localhost:3000`
- Backend URL: `http://127.0.0.1:8000`

### Production Environment
- Hostname: Contains `legatoo.westlinktowing.com`
- Frontend URL: `https://legatoo.westlinktowing.com`
- Backend URL: `https://api.legatoo.westlinktowing.com`

## Benefits

1. **Single Source of Truth**: All URLs managed from one place
2. **Environment Awareness**: Automatic detection of dev/prod environments
3. **Easy Maintenance**: Change URLs in one place, updates everywhere
4. **Consistency**: Ensures all components use the same URLs
5. **Flexibility**: Easy to override URLs via environment variables

## Migration Notes

### Before (Hardcoded URLs)
```javascript
// Old way - hardcoded URLs
this.apiBase = 'http://127.0.0.1:8000/api/v1/auth';
window.location.href = 'https://legatoo.westlinktowing.com/auth/login';
```

### After (Centralized URLs)
```javascript
// New way - centralized URLs
this.apiBase = window.urlConfig.apiUrls.authBase;
window.location.href = window.urlConfig.authUrls.login;
```

## Deployment

### Development
1. No changes needed - uses default localhost URLs
2. URLs automatically detected based on hostname

### Production
1. Set environment variables:
   ```env
   ENVIRONMENT=production
   FRONTEND_URL=https://legatoo.westlinktowing.com
   BACKEND_URL=https://api.legatoo.westlinktowing.com
   ```
2. Deploy all files including `url-config.js`
3. URLs automatically switch to production values

## Testing

To verify the configuration is working:

1. **Backend**: Check that email service uses correct URLs
2. **Frontend**: Verify all links and API calls use centralized URLs
3. **Environment**: Test both development and production URL generation

## Future Enhancements

- Add URL validation
- Support for custom domains
- Dynamic URL generation based on user preferences
- URL analytics and monitoring
