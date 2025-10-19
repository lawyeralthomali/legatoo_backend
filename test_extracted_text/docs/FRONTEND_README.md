# Frontend Email Verification & Password Reset Pages

This directory contains the frontend pages for handling email verification and password reset flows.

## 📁 Files Created

### 1. `email-verification.html`
**Purpose**: Handles email verification when users click the verification link from their email.

**Features**:
- ✅ Extracts token from URL automatically
- ✅ Calls backend API to verify email
- ✅ Shows success/error messages
- ✅ **5-second countdown timer** with auto-redirect to login
- ✅ Manual "Go to Login" button
- ✅ Professional Legatoo Westlink Towing branding
- ✅ Responsive design for mobile/desktop

**URL Format**: `http://localhost:3000/email-verification.html?token=VERIFICATION_TOKEN`

### 2. `login.html`
**Purpose**: Login page where users are redirected after email verification.

**Features**:
- ✅ Email and password login form
- ✅ Calls backend API for authentication
- ✅ Stores JWT tokens in localStorage
- ✅ Redirects to dashboard after successful login
- ✅ "Forgot Password" and "Create Account" links
- ✅ Professional Legatoo Westlink Towing branding

### 3. `password-reset.html`
**Purpose**: Handles password reset when users click the reset link from their email.

**Features**:
- ✅ Extracts token from URL automatically
- ✅ Password strength validation
- ✅ Confirms password matching
- ✅ Calls backend API to reset password
- ✅ Shows success message with redirect to login
- ✅ Professional Legatoo Westlink Towing branding

**URL Format**: `http://localhost:3000/password-reset.html?token=RESET_TOKEN`

## 🚀 How It Works

### Email Verification Flow:
1. **User Signs Up** → Backend sends verification email via Hostinger SMTP
2. **User Receives Email** → Email contains link to `email-verification.html?token=...`
3. **User Clicks Link** → Frontend page loads and extracts token
4. **Frontend Calls API** → `POST /api/v1/auth/verify-email?verification_token=...`
5. **Success Response** → Shows success message with 5-second countdown
6. **Auto Redirect** → Automatically redirects to `login.html` after 5 seconds
7. **Manual Option** → User can click "Go to Login" button immediately

### Password Reset Flow:
1. **User Requests Reset** → Backend sends reset email via Hostinger SMTP
2. **User Receives Email** → Email contains link to `password-reset.html?token=...`
3. **User Clicks Link** → Frontend page loads and extracts token
4. **User Enters New Password** → Frontend validates password strength
5. **Frontend Calls API** → `POST /api/v1/auth/confirm-password-reset`
6. **Success Response** → Shows success message with redirect to login

## 🔧 Configuration

### Backend Configuration (supabase.env):
```env
# Frontend URL - Update this for production
FRONTEND_URL=http://localhost:3000

# SMTP Configuration (Hostinger)
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=587
SMTP_USERNAME=info@legatoo.westlinktowing.com
SMTP_PASSWORD=Zaq1zaq1zaq@@
FROM_EMAIL=info@legatoo.westlinktowing.com
FROM_NAME=Legatoo Westlink Towing
```

### Frontend Configuration:
- Update API base URL in JavaScript if backend is on different port
- Update redirect URLs for production deployment
- Update branding/colors as needed

## 📧 Email Templates

The backend automatically generates professional HTML emails with:
- **Legatoo Westlink Towing branding**
- **Professional styling**
- **Clear call-to-action buttons**
- **Security notices**
- **Both HTML and text versions**

## 🎨 Customization

### Colors & Branding:
- **Primary Green**: `#4CAF50` (success, login)
- **Primary Red**: `#e74c3c` (password reset)
- **Logo**: "L" in circle (update as needed)
- **Company Name**: "Legatoo Westlink Towing"

### Timer Settings:
- **Countdown**: 5 seconds (configurable in JavaScript)
- **Auto-redirect**: To `/login` page

## 🚀 Deployment

### For Production:
1. **Update FRONTEND_URL** in `supabase.env` to your production domain
2. **Deploy HTML files** to your web server
3. **Update API URLs** in JavaScript if needed
4. **Configure HTTPS** for security
5. **Update CORS settings** in backend

### Example Production URLs:
- `https://yourdomain.com/email-verification.html?token=...`
- `https://yourdomain.com/password-reset.html?token=...`
- `https://yourdomain.com/login`

## ✅ Testing

Run the test script to verify everything works:
```bash
py test_frontend_flow.py
```

This will:
- Test signup with frontend URLs
- Test password reset with frontend URLs
- Verify email verification endpoint
- Confirm all flows are working correctly

## 🔒 Security Features

- **Token Validation**: Tokens are validated server-side
- **Password Strength**: Enforced on both frontend and backend
- **HTTPS Ready**: All forms use secure submission
- **Token Expiry**: 1-hour expiry for reset tokens
- **No Token Exposure**: Tokens are handled securely

## 📱 Mobile Responsive

All pages are fully responsive and work on:
- Desktop computers
- Tablets
- Mobile phones
- Different screen sizes

The design adapts automatically to different screen sizes with appropriate styling and layout adjustments.
