#!/bin/bash
# Production Deployment Script for Legatoo Backend
# Updated for http://srv1022733.hstgr.cloud:8000
# 
# IMPORTANT: This script uses placeholder values for security.
# Replace all placeholder values with your actual production credentials.

echo "🚀 Deploying Legatoo Backend to Production..."

# Load environment variables from .env.production file
if [ -f ".env.production" ]; then
    echo "📄 Loading environment variables from .env.production..."
    export $(cat .env.production | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env.production file not found!"
    echo "📝 Please create .env.production with your actual production credentials"
    echo "📋 See .env.production.example for reference"
    exit 1
fi

# Set production environment variables (these are safe to expose)
export ENVIRONMENT=production
export BACKEND_URL=http://srv1022733.hstgr.cloud:8000
export FRONTEND_URL=https://legatoo.westlinktowing.com
export CORS_ORIGINS=https://legatoo.westlinktowing.com,https://www.legatoo.westlinktowing.com,http://srv1022733.hstgr.cloud:8000

# Database configuration
export DATABASE_URL=sqlite+aiosqlite:///./app.db

# Debug mode (disabled in production)
export DEBUG=False

echo "✅ Environment variables set for production"
echo "🌐 Backend URL: $BACKEND_URL"
echo "🔗 Frontend URL: $FRONTEND_URL"
echo "🔒 CORS Origins: $CORS_ORIGINS"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
python -m alembic upgrade head

# Start the server
echo "🚀 Starting production server..."
echo "📍 Server will be available at: $BACKEND_URL"
echo "📚 API Documentation: $BACKEND_URL/docs"

# Start with production settings
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
