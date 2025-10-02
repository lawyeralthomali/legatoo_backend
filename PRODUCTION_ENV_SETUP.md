# 🚀 Production Deployment Guide

## 📋 Server Environment File Setup

### Step 1: Create `.env` file on your server

Copy the contents from `production.env` and create a `.env` file on your server:

```bash
# On your server, create the .env file
nano .env
```

### Step 2: Copy the production configuration

Paste the following content into your `.env` file:

```bash
# ===========================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ===========================================

# ===========================================
# SMTP Configuration for Email Verification
# ===========================================
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=587
SMTP_USERNAME=legatoo@althomalilawfirm.sa
SMTP_PASSWORD=Zaq1zaq1zaq@@
FROM_EMAIL=legatoo@althomalilawfirm.sa
FROM_NAME=Legatoo App

# ===========================================
# Application Configuration
# ===========================================
APP_NAME=Legatoo Westlink Towing
FRONTEND_URL=https://legatoo.westlinktowing.com
BACKEND_URL=https://api.westlinktowing.com
ENVIRONMENT=production

# ===========================================
# Database Configuration
# ===========================================
DATABASE_URL=sqlite+aiosqlite:///./app.db

# ===========================================
# Security Configuration
# ===========================================
# JWT Secret Keys (IMPORTANT: Change these in production!)
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-legatoo-2024
SUPABASE_JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-legatoo-2024
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-legatoo-2024

# Encryption Key for Enjaz Credentials
ENCRYPTION_KEY=vb2WSk_hPSbvQlDvfZQmxEDg6q_slPfxY73fqZpEOP0=

# ===========================================
# Admin Configuration
# ===========================================
SUPER_ADMIN_EMAIL=legatoo@althomalilawfirm.sa
SUPER_ADMIN_PASSWORD=Zaq1zaq1

# ===========================================
# CORS Configuration
# ===========================================
# Allowed origins for CORS (comma-separated)
CORS_ORIGINS=https://legatoo.westlinktowing.com,https://api.westlinktowing.com,http://localhost:3000,http://127.0.0.1:3000,http://192.168.100.109:3000,http://srv1022733.hstgr.cloud:8000,https://srv1022733.hstgr.cloud:8000,http://srv1022733.hstgr.cloud,https://srv1022733.hstgr.cloud

# ===========================================
# Server Configuration
# ===========================================
# Host and port for the server
HOST=0.0.0.0
PORT=8000

# ===========================================
# Logging Configuration
# ===========================================
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
ERROR_LOG_FILE=logs/errors.log

# ===========================================
# Additional Production Settings
# ===========================================
# Disable debug mode in production
DEBUG=False

# Enable SSL/TLS
SSL_ENABLED=True

# Session configuration
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# ===========================================
# Performance Configuration
# ===========================================
# Worker processes (adjust based on your server)
WORKERS=4

# Request timeout
REQUEST_TIMEOUT=30

# ===========================================
# Monitoring and Health Checks
# ===========================================
HEALTH_CHECK_ENABLED=True
METRICS_ENABLED=True
```

### Step 3: Set proper file permissions

```bash
# Make sure the .env file is secure
chmod 600 .env
chown www-data:www-data .env
```

### Step 4: Verify the configuration

```bash
# Check if the environment variables are loaded correctly
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Environment loaded:', os.getenv('ENVIRONMENT'))"
```

## 🔧 Important Notes

### Security Considerations:
1. **Change JWT Secrets**: Generate new, secure JWT secrets for production
2. **File Permissions**: Ensure `.env` file has restricted permissions (600)
3. **Database Security**: Consider using a more secure database in production
4. **SSL/TLS**: Ensure your server has proper SSL certificates

### Generate New JWT Secrets:
```bash
# Generate a new secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Database Migration:
```bash
# Run database migrations
alembic upgrade head
```

### Start the Server:
```bash
# Start the production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 File Structure on Server:
```
/your/project/path/
├── .env                    # Production environment file
├── app/                   # Application code
├── logs/                  # Log files directory
├── uploads/               # File uploads directory
├── app.db                 # SQLite database
├── requirements.txt       # Python dependencies
└── run.py                # Application entry point
```

## 🚨 Troubleshooting:

1. **Email not working**: Check SMTP credentials and server settings
2. **CORS errors**: Verify CORS_ORIGINS includes your frontend domain
3. **Database issues**: Ensure database file permissions are correct
4. **SSL issues**: Verify SSL certificates are properly configured

## 📞 Support:
If you encounter any issues, check the logs in the `logs/` directory for error details.
