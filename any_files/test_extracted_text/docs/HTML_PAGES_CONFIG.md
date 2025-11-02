# HTML Pages Configuration for Production

## 🌐 Updated HTML Files for Production Backend

Both `password-reset.html` and `email-verification.html` have been updated to work with your production backend at `http://srv1022733.hstgr.cloud:8000`.

## 📁 Files Updated

### 1. `password-reset.html`
- ✅ Updated API base URL to production backend
- ✅ Dynamic frontend URL configuration
- ✅ Automatic environment detection

### 2. `email-verification.html`
- ✅ Updated API base URL to production backend
- ✅ Dynamic frontend URL configuration
- ✅ Automatic environment detection

### 3. `app-config.js` (New)
- ✅ Dynamic configuration script
- ✅ Automatic environment detection
- ✅ Centralized URL management

## 🔧 How It Works

### Dynamic Configuration
The HTML files now use `app-config.js` which automatically detects the environment:

```javascript
// Automatically detects environment based on domain
const config = {
    getEnvironment: function() {
        const hostname = window.location.hostname;
        
        if (hostname.includes('srv1022733.hstgr.cloud')) {
            return 'production';
        } else if (hostname.includes('localhost')) {
            return 'development';
        } else {
            return 'production'; // Default
        }
    }
};
```

### API Endpoints
Based on the environment, the correct API endpoints are used:

**Production:**
- API Base: `http://srv1022733.hstgr.cloud:8000/api/v1/auth`
- Frontend: `https://legatoo.westlinktowing.com`

**Development:**
- API Base: `http://127.0.0.1:8000/api/v1/auth`
- Frontend: `http://localhost:3000`

## 🔐 Authentication Flow

### Password Reset Flow
1. User receives password reset email with token
2. User clicks link: `https://legatoo.westlinktowing.com/password-reset.html?token=ABC123`
3. HTML page automatically detects production environment
4. Makes API call to: `http://srv1022733.hstgr.cloud:8000/api/v1/auth/confirm-password-reset`
5. On success, redirects to: `https://legatoo.westlinktowing.com/auth/login/`

### Email Verification Flow
1. User receives verification email with token
2. User clicks link: `https://legatoo.westlinktowing.com/email-verification.html?token=XYZ789`
3. HTML page automatically detects production environment
4. Makes API call to: `http://srv1022733.hstgr.cloud:8000/api/v1/auth/verify-email`
5. On success, redirects to: `https://legatoo.westlinktowing.com/auth/login/`

## 📱 Usage Examples

### Password Reset Request
```javascript
// The HTML page automatically uses the correct API URL
const response = await fetch(`${this.apiBase}/confirm-password-reset`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ 
        reset_token: this.token, 
        new_password: password 
    })
});
```

### Email Verification Request
```javascript
// The HTML page automatically uses the correct API URL
const response = await fetch(`${this.apiBase}/verify-email?verification_token=${this.token}`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    }
});
```

## 🚀 Deployment

### For Production
1. Upload all three files to your web server:
   - `password-reset.html`
   - `email-verification.html`
   - `app-config.js`

2. Ensure they're accessible at:
   - `https://legatoo.westlinktowing.com/password-reset.html`
   - `https://legatoo.westlinktowing.com/email-verification.html`
   - `https://legatoo.westlinktowing.com/app-config.js`

### For Development
The same files will automatically work in development by detecting `localhost` in the domain.

## 🔍 Testing

### Test Password Reset
1. Send password reset email from your backend
2. Click the reset link in the email
3. Verify it connects to: `http://srv1022733.hstgr.cloud:8000/api/v1/auth/confirm-password-reset`

### Test Email Verification
1. Send verification email from your backend
2. Click the verification link in the email
3. Verify it connects to: `http://srv1022733.hstgr.cloud:8000/api/v1/auth/verify-email`

## 🛡️ Security Features

- ✅ **Environment Detection**: Automatically uses correct URLs
- ✅ **Token Validation**: Validates tokens from URL parameters
- ✅ **Password Requirements**: Enforces strong password policies
- ✅ **Error Handling**: Comprehensive error messages
- ✅ **CORS Support**: Works with your production CORS settings

## 📋 Configuration Summary

| Environment | API Base URL | Frontend URL |
|-------------|--------------|--------------|
| Production | `http://srv1022733.hstgr.cloud:8000/api/v1/auth` | `https://legatoo.westlinktowing.com` |
| Development | `http://127.0.0.1:8000/api/v1/auth` | `http://localhost:3000` |

Your HTML pages are now fully configured for production and will automatically work with your backend at `http://srv1022733.hstgr.cloud:8000`! 🎉
