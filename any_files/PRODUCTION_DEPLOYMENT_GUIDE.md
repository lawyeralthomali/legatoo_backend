# Production Deployment Guide for api.westlinktowing.com

## 📋 Overview

This guide covers deploying your FastAPI application with the Legal AI Assistant to your production server at `https://api.westlinktowing.com`.

## 🔧 Step 1: SSH into Production Server

```bash
ssh your-username@srv1022733.hstgr.cloud
# Or use your specific SSH credentials
```

## 📝 Step 2: Create/Update Environment File

Navigate to your project directory and create the `.env` file:

```bash
cd /path/to/your/project
nano .env
```

Paste the following configuration:

```env
# SMTP Configuration for Email Verification (Hostinger)
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=587
SMTP_USERNAME=Legatoo@altohmalilawfirm.sa
SMTP_PASSWORD=Zaq1zaq1zaq@@
FROM_EMAIL=Legatoo@altohmalilawfirm.sa
FROM_NAME=Legatoo App

# App Configuration
APP_NAME=Legatoo Westlink Towing
FRONTEND_URL=https://legatoo.westlinktowing.com

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./app.db

# JWT Secret (CRITICAL: Change in production!)
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-legatoo-2024
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-legatoo-2024

# Encryption Key for Enjaz Credentials
ENCRYPTION_KEY=vb2WSk_hPSbvQlDvfZQmxEDg6q_slPfxY73fqZpEOP0=

# Super Admin Credentials
SUPER_ADMIN_EMAIL=info@legatoo.westlinktowing.com
SUPER_ADMIN_PASSWORD=Zaq1zaq1

# CORS Origins
CORS_ORIGINS=https://legatoo.westlinktowing.com,https://api.westlinktowing.com,http://localhost:3000

# OpenAI API Key (Optional - for Legal AI Assistant)
# OPENAI_API_KEY=your-openai-api-key-here

# Legal Assistant Configuration
UPLOAD_DIR=uploads/legal_documents
EMBEDDING_MODEL=text-embedding-3-large

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

Save the file: `Ctrl+X`, then `Y`, then `Enter`

## 🚀 Step 3: Deploy Code Changes

```bash
# Pull latest changes from Git
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Or if using virtual environment:
source venv/bin/activate  # Activate venv first
pip install -r requirements.txt
```

## 📦 Step 4: Run Database Migration

```bash
# Run Alembic migrations for Legal AI Assistant tables
alembic upgrade head
```

## 🔄 Step 5: Restart the Service

### If using systemd:
```bash
sudo systemctl restart fastapi-app
# Or your specific service name
sudo systemctl status fastapi-app
```

### If using PM2:
```bash
pm2 restart all
pm2 logs
```

### If using screen/tmux:
```bash
# Find and kill the existing process
ps aux | grep uvicorn
kill -9 <process-id>

# Start in screen
screen -S fastapi
cd /path/to/your/project
source venv/bin/activate  # if using venv
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Detach: Ctrl+A then D
```

### If using supervisor:
```bash
sudo supervisorctl restart fastapi-app
sudo supervisorctl status
```

## ✅ Step 6: Verify Deployment

### Test API Health:
```bash
curl https://api.westlinktowing.com/health
```

Should return:
```json
{"status": "healthy", "service": "sqlite-auth-fastapi"}
```

### Test Legal Assistant Endpoints:
```bash
curl https://api.westlinktowing.com/ | jq .endpoints.legal_assistant
```

Should show:
```json
{
  "upload": "/api/v1/legal-assistant/documents/upload",
  "search": "/api/v1/legal-assistant/documents/search",
  "documents": "/api/v1/legal-assistant/documents",
  "statistics": "/api/v1/legal-assistant/statistics"
}
```

### Test Email Configuration:
```bash
# Test SMTP connection with Python
python3 << EOF
import os
from dotenv import load_dotenv
load_dotenv()

import smtplib

smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_username = os.getenv("SMTP_USERNAME")
smtp_password = os.getenv("SMTP_PASSWORD")

print(f"Testing SMTP: {smtp_server}:{smtp_port}")
print(f"Username: {smtp_username}")

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.quit()
    print("✅ SMTP connection successful!")
except Exception as e:
    print(f"❌ SMTP error: {e}")
EOF
```

## 🔍 Step 7: Monitor Logs

### Check application logs:
```bash
# If using systemd:
sudo journalctl -u fastapi-app -f

# If using PM2:
pm2 logs

# If in screen:
screen -r fastapi
```

### Check for email errors:
```bash
tail -f logs/app.log | grep -i email
tail -f logs/errors.log
```

## 🐛 Troubleshooting

### Email Authentication Fails

If you see: `authentication failed: (reason unavailable)`

**Solutions:**
1. Verify SMTP credentials are correct
2. Check Hostinger email account is active
3. Try testing with a different SMTP server (Gmail, SendGrid)
4. Ensure port 587 is open on your server

### CORS Errors Persist

If frontend still has CORS issues:
1. Verify `.env` file has `CORS_ORIGINS` set correctly
2. Restart the service completely (not just reload)
3. Clear browser cache
4. Check server logs for CORS warnings

### Database Migration Fails

```bash
# Check current migration version
alembic current

# If needed, reset and upgrade
alembic downgrade base
alembic upgrade head
```

### Service Won't Start

```bash
# Check if port 8000 is in use
sudo lsof -i :8000

# Kill any existing process
sudo kill -9 <process-id>

# Check for Python errors
python3 -c "from app.main import app; print('OK')"
```

## 📊 Expected Results

After successful deployment:

1. ✅ API accessible at: https://api.westlinktowing.com
2. ✅ Docs at: https://api.westlinktowing.com/docs
3. ✅ CORS allows: https://legatoo.westlinktowing.com
4. ✅ Email verification sends from: Legatoo@altohmalilawfirm.sa
5. ✅ Legal AI Assistant endpoints available
6. ✅ No authentication errors in logs

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=false` in production
- [ ] Secure `.env` file permissions: `chmod 600 .env`
- [ ] Enable HTTPS (already done ✅)
- [ ] Keep SMTP password secure
- [ ] Regular security updates: `pip install --upgrade -r requirements.txt`

## 📞 Support

If issues persist:
1. Check logs: `tail -f logs/app.log logs/errors.log`
2. Verify environment variables are loaded: `python3 -c "import os; print(os.getenv('SMTP_USERNAME'))"`
3. Test locally first with same configuration
4. Contact Hostinger support if SMTP issues continue

---

**Last Updated:** 2025-10-01
**Server:** srv1022733.hstgr.cloud
**Domain:** https://api.westlinktowing.com

