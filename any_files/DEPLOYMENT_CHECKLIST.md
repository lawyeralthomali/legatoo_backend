# 🚀 Production Deployment Checklist

## ✅ Changes Made (Completed)

### 1. Configuration Files Updated

#### ✅ `app-config.js`
- ✅ Updated production API URL: `https://api.westlinktowing.com`
- ✅ Added domain detection for `westlinktowing.com`

#### ✅ `frontend-config.js`
- ✅ Updated all endpoints to use `https://api.westlinktowing.com`
- ✅ Updated Legal Assistant endpoints to new implementation

#### ✅ `url-config.js`
- ✅ Fixed production backend URL: `https://api.westlinktowing.com`

#### ✅ `app/main.py`
- ✅ Fixed CORS to include production domains
- ✅ Properly imported Legal AI Assistant models
- ✅ Legal Assistant routes registered

#### ✅ `supabase.env`
- ✅ Frontend URL updated to: `https://legatoo.westlinktowing.com`
- ✅ CORS origins updated with production domains
- ✅ Email SMTP configured (Hostinger)

#### ✅ `app/models/profile.py`
- ✅ Uncommented `uploaded_documents` relationship for Legal AI Assistant

---

## 📋 Production Deployment Steps

### Step 1: Commit and Push Changes

```bash
# Add all changes
git add .

# Commit
git commit -m "Production deployment: Update URLs, fix CORS, add Legal AI Assistant"

# Push to repository
git push origin main
```

### Step 2: Deploy to Production Server

**SSH into your server:**
```bash
ssh your-user@srv1022733.hstgr.cloud
cd /path/to/your/project
```

**Pull latest changes:**
```bash
git pull origin main
```

**Install dependencies:**
```bash
# If using virtual environment
source venv/bin/activate

# Install new packages
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

**Create/Update `.env` file on server:**
```bash
nano .env
```

**Add this configuration:**
```env
# SMTP Configuration (Hostinger)
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=587
SMTP_USERNAME=Legatoo@altohmalilawfirm.sa
SMTP_PASSWORD=Zaq1zaq1zaq@@
FROM_EMAIL=Legatoo@altohmalilawfirm.sa
FROM_NAME=Legatoo App

# App Configuration
APP_NAME=Legatoo Westlink Towing
FRONTEND_URL=https://legatoo.westlinktowing.com

# Database
DATABASE_URL=sqlite+aiosqlite:///./app.db

# JWT Secret
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-legatoo-2024
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-legatoo-2024

# Encryption Key
ENCRYPTION_KEY=vb2WSk_hPSbvQlDvfZQmxEDg6q_slPfxY73fqZpEOP0=

# Super Admin
SUPER_ADMIN_EMAIL=info@legatoo.westlinktowing.com
SUPER_ADMIN_PASSWORD=Zaq1zaq1

# CORS (Production domains first!)
CORS_ORIGINS=https://legatoo.westlinktowing.com,https://api.westlinktowing.com,http://localhost:3000

# Legal AI Assistant (Optional)
UPLOAD_DIR=uploads/legal_documents
# OPENAI_API_KEY=your-key-here-for-best-results

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 4: Run Database Migration

```bash
# Run migrations for Legal AI Assistant tables
alembic upgrade head
```

### Step 5: Create Upload Directory

```bash
# Create directory for legal document uploads
mkdir -p uploads/legal_documents
chmod 755 uploads/legal_documents
```

### Step 6: Restart Server

**Choose your deployment method:**

```bash
# If using PM2:
pm2 restart all
pm2 logs

# If using systemd:
sudo systemctl restart your-fastapi-service
sudo systemctl status your-fastapi-service

# If using screen:
screen -r fastapi  # Attach to session
# Ctrl+C to stop
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Ctrl+A then D to detach
```

---

## ✅ Verification Checklist

After deployment, verify everything works:

### 1. Test API Health
```bash
curl https://api.westlinktowing.com/health
# Expected: {"status": "healthy", "service": "sqlite-auth-fastapi"}
```

### 2. Test CORS
Open browser console on `https://legatoo.westlinktowing.com` and run:
```javascript
fetch('https://api.westlinktowing.com/health')
  .then(r => r.json())
  .then(d => console.log('✅ CORS working!', d))
  .catch(e => console.error('❌ CORS error:', e));
```

### 3. Test Email Verification
- Sign up a new user from your frontend
- Check server logs for: `Email sent successfully to...`

```bash
tail -f logs/app.log | grep -i email
```

### 4. Test Legal AI Assistant
```bash
curl https://api.westlinktowing.com/ | jq .endpoints.legal_assistant
```

Expected output:
```json
{
  "upload": "/api/v1/legal-assistant/documents/upload",
  "search": "/api/v1/legal-assistant/documents/search",
  "documents": "/api/v1/legal-assistant/documents",
  "statistics": "/api/v1/legal-assistant/statistics"
}
```

### 5. Check All Endpoints
Visit: `https://api.westlinktowing.com/docs`

Verify:
- ✅ Authentication endpoints work
- ✅ Legal Assistant section visible
- ✅ All 11 Legal Assistant endpoints present
- ✅ Can authenticate with test credentials

---

## 🔧 Common Issues and Solutions

### Issue: CORS Still Blocking

**Solution:**
1. Clear browser cache completely
2. Verify `.env` file has `CORS_ORIGINS` set correctly
3. Restart server (not just reload)
4. Check `Access-Control-Allow-Origin` header in browser network tab

### Issue: Email Verification Fails

**Solution:**
1. Test SMTP connection:
```bash
python3 << EOF
import smtplib
server = smtplib.SMTP('smtp.hostinger.com', 587)
server.starttls()
server.login('Legatoo@altohmalilawfirm.sa', 'Zaq1zaq1zaq@@')
server.quit()
print('✅ SMTP works!')
EOF
```

2. Check email account is active
3. Verify port 587 is open: `telnet smtp.hostinger.com 587`
4. Check server logs for specific error

### Issue: Database Tables Missing

**Solution:**
```bash
# Check migration status
alembic current

# If needed, run migrations
alembic upgrade head

# Verify tables exist
sqlite3 app.db ".tables"
# Should see: legal_documents, legal_document_chunks
```

### Issue: Legal Assistant Import Error

**Solution:**
```bash
# Install missing dependencies
pip install python-docx numpy openai

# Test imports
python3 -c "from app.main import app; print('OK')"
```

---

## 📊 Production URLs Reference

### Frontend (User-facing)
- **Main Site:** https://legatoo.westlinktowing.com
- **Login:** https://legatoo.westlinktowing.com/auth/login
- **Signup:** https://legatoo.westlinktowing.com/auth/signup

### Backend (API)
- **API Base:** https://api.westlinktowing.com
- **API Docs:** https://api.westlinktowing.com/docs
- **Health Check:** https://api.westlinktowing.com/health

### Email Configuration
- **SMTP Server:** smtp.hostinger.com:587
- **From Email:** Legatoo@altohmalilawfirm.sa
- **Verification Links:** Point to https://legatoo.westlinktowing.com

---

## 🎯 Success Criteria

Deployment is successful when:

- ✅ API responds at https://api.westlinktowing.com
- ✅ Frontend can access API without CORS errors
- ✅ Email verification emails are sent successfully
- ✅ Legal AI Assistant endpoints are accessible
- ✅ No errors in server logs
- ✅ Users can sign up, login, and verify email
- ✅ HTTPS working on both domains
- ✅ Database migrations applied

---

## 📞 Support

If issues persist:
1. Check logs: `tail -f logs/app.log logs/errors.log`
2. Verify environment variables loaded: `python3 -c "import os; print(os.getenv('SMTP_USERNAME'))"`
3. Test each component individually
4. Review `PRODUCTION_DEPLOYMENT_GUIDE.md` for detailed troubleshooting

---

**Last Updated:** 2025-10-01  
**Deployment Target:** https://api.westlinktowing.com  
**Status:** Ready for Deployment ✅

