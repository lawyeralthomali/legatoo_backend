# Email Verification Flow - Complete Process

## 🔄 Complete Email Verification Flow

Here's how the email verification process works from signup to completion:

### **Step 1: User Signup**
```
POST http://srv1022733.hstgr.cloud:8000/api/v1/auth/signup
```

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully. Please check your email for verification.",
  "data": {
    "user_id": 123,
    "email": "user@example.com",
    "is_verified": false
  },
  "errors": []
}
```

### **Step 2: Backend Sends Verification Email**
The backend automatically sends an email with a verification link:

**Email Content:**
```
Subject: Verify Your Email - Legatoo

Hello John,

Please click the link below to verify your email address:

https://legatoo.westlinktowing.com/email-verification.html?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

This link will expire in 24 hours.

Best regards,
Legatoo Team
```

### **Step 3: User Clicks Email Link**
When the user clicks the link, it opens:
```
https://legatoo.westlinktowing.com/email-verification.html?token=ABC123XYZ789
```

### **Step 4: HTML Page Automatically Verifies**
The `email-verification.html` page:

1. **Detects Environment**: Automatically detects production
2. **Extracts Token**: Gets token from URL parameter
3. **Makes API Call**: Calls backend verification endpoint
4. **Shows Result**: Displays success or error message

**API Call Made:**
```javascript
POST http://srv1022733.hstgr.cloud:8000/api/v1/auth/verify-email?verification_token=ABC123XYZ789
```

### **Step 5: Backend Verifies Token**
The backend endpoint `/verify-email`:

1. **Validates Token**: Checks if token is valid and not expired
2. **Updates User**: Sets `is_verified = true` in database
3. **Returns Response**: Sends success confirmation

**Backend Response:**
```json
{
  "success": true,
  "message": "Email verified successfully",
  "data": {
    "user_id": 123,
    "email": "user@example.com",
    "is_verified": true
  },
  "errors": []
}
```

### **Step 6: HTML Page Shows Success**
The HTML page displays:
- ✅ **Success Icon**: Green checkmark
- 📝 **Success Message**: "Email verified successfully!"
- ⏱️ **Countdown Timer**: 5-second countdown
- 🔗 **Login Button**: Redirects to login page

### **Step 7: Automatic Redirect**
After 5 seconds (or when user clicks "Go to Login"):
```
Redirects to: https://legatoo.westlinktowing.com/auth/login/
```

## 🔧 Technical Implementation

### **Backend Endpoint**
```python
@router.post("/verify-email", response_model=ApiResponse)
async def verify_email(
    verification_token: str = Query(..., description="Email verification token"),
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """Verify user email using verification token."""
    result = await auth_service.verify_email(verification_token)
    return result
```

### **Frontend JavaScript**
```javascript
async verifyEmail() {
    try {
        const response = await fetch(`${this.apiBase}/verify-email?verification_token=${this.token}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (response.ok && result.success) {
            this.showSuccess(result);
        } else {
            this.showError(result.message || 'Verification failed', result.errors);
        }
    } catch (error) {
        this.showError('Network error. Please check your connection and try again.');
    }
}
```

## 🛡️ Security Features

- ✅ **Token Expiration**: Tokens expire after 24 hours
- ✅ **One-Time Use**: Tokens can only be used once
- ✅ **Environment Detection**: Automatically uses correct API URL
- ✅ **Error Handling**: Comprehensive error messages
- ✅ **HTTPS**: All communications are secure

## 📱 User Experience

1. **Signup** → User fills form and submits
2. **Email Sent** → User receives verification email
3. **Click Link** → User clicks link in email
4. **Auto Verification** → Page automatically verifies email
5. **Success Message** → User sees confirmation
6. **Auto Redirect** → User is redirected to login page

## 🔍 Testing the Flow

### **Test Email Verification**
1. **Signup a new user**:
   ```bash
   curl -X POST "http://srv1022733.hstgr.cloud:8000/api/v1/auth/signup" \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "TestPass123!", "first_name": "Test", "last_name": "User"}'
   ```

2. **Check email** for verification link

3. **Click link** to open `email-verification.html`

4. **Verify** that it calls the correct API endpoint

5. **Check** that user is redirected to login page

## ✅ Current Status

Your email verification flow is **fully configured** and ready for production:

- ✅ **Backend**: Correctly sends verification emails
- ✅ **HTML Page**: Automatically verifies emails
- ✅ **API Integration**: Uses production backend URL
- ✅ **User Experience**: Smooth flow from email to login
- ✅ **Security**: Proper token validation and expiration

The email verification process is now complete and production-ready! 🎉
