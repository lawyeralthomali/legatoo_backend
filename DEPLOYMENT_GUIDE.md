# Deployment Guide

## Overview
This deployment system provides a clean, lightweight CI/CD pipeline for the FastAPI backend.

## Files Created

### 1. `.github/workflows/deploy-backend.yml`
- **Purpose**: GitHub Actions workflow for automated deployment
- **Triggers**: Push to `main` branch or manual workflow dispatch
- **Actions**: 
  - Checkout code
  - SSH into server
  - Run deployment script

### 2. `deploy.sh`
- **Purpose**: Main deployment script
- **Features**:
  - Lightweight and focused
  - Idempotent (safe to run multiple times)
  - Automatic virtual environment management
  - Clean process management
  - Comprehensive logging

## Setup Instructions

### 1. GitHub Secrets Configuration
Add these secrets to your GitHub repository:

```
HOSTINGER_HOST=your-server-ip
HOSTINGER_USERNAME=root
HOSTINGER_SSH_KEY=your-private-ssh-key
HOSTINGER_PORT=22
```

### 2. Server Setup
On your server, ensure you have:
- Python 3.8+ installed
- SSH access configured
- Project directory: `~/legatoo_backend`

### 3. Make Script Executable
```bash
chmod +x deploy.sh
```

## Usage

### Automated Deployment (GitHub Actions)
1. Push code to `main` branch
2. GitHub Actions automatically deploys
3. Check the Actions tab for deployment status

### Manual Deployment
```bash
# SSH into server
ssh root@your-server

# Navigate to project directory
cd ~/legatoo_backend

# Run deployment script
./deploy.sh
```

## What the Deployment Script Does

1. **Environment Check**: Verifies it's in the correct directory
2. **Virtual Environment**: Creates venv if it doesn't exist
3. **Dependencies**: Installs/updates packages from requirements.txt
4. **Code Update**: Pulls latest code from git (if repository exists)
5. **Process Management**: 
   - Stops existing uvicorn processes
   - Starts new process in background
   - Saves PID to app.pid
6. **Health Check**: Verifies application started successfully
7. **Logging**: Provides clear status messages and log locations

## Process Management

### Stop Application
```bash
kill $(cat app.pid)
```

### View Logs
```bash
tail -f logs/app.log
```

### Restart Application
```bash
./deploy.sh
```

## Features

- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Lightweight**: No unnecessary system package installation
- ✅ **Clean**: Proper process management and logging
- ✅ **Flexible**: Works with or without git repository
- ✅ **Robust**: Error handling and health checks
- ✅ **Manual Friendly**: Easy to run via SSH

## Troubleshooting

### Application Won't Start
1. Check logs: `tail -f logs/app.log`
2. Verify port 8000 is available: `netstat -tlnp | grep 8000`
3. Check environment file: `cat .env.production`

### Permission Issues
```bash
chmod +x deploy.sh
```

### Virtual Environment Issues
```bash
rm -rf venv
./deploy.sh  # Will recreate venv
```

## Environment Variables Required

Ensure `.env.production` exists with:
- `ENVIRONMENT=production`
- `SECRET_KEY=your-secret-key`
- `SUPABASE_JWT_SECRET=your-jwt-secret`
- `JWT_SECRET=your-jwt-secret`
- Other required variables...

## Success Indicators

After successful deployment:
- ✅ Process running: `ps aux | grep uvicorn`
- ✅ Health check: `curl http://localhost:8000/health`
- ✅ API docs: `http://your-server:8000/docs`
- ✅ Logs: `tail -f logs/app.log`
