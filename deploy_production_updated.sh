#!/bin/bash
# Production Deployment Script for Legatoo Backend
# Updated for http://srv1022733.hstgr.cloud:8000
# 
# IMPORTANT: This script uses placeholder values for security.
# Replace all placeholder values with your actual production credentials.

echo "🚀 Deploying Legatoo Backend to Production..."

# Set production environment variables (these are safe to expose)
export ENVIRONMENT=production
export BACKEND_URL=http://srv1022733.hstgr.cloud:8000
export FRONTEND_URL=https://legatoo.westlinktowing.com
export CORS_ORIGINS=https://legatoo.westlinktowing.com,https://www.legatoo.westlinktowing.com,http://srv1022733.hstgr.cloud:8000

# Database configuration
export DATABASE_URL=sqlite+aiosqlite:///./app.db

# JWT Configuration (Replace with your actual secrets)
export SECRET_KEY=your-secret-key-here
export SUPABASE_JWT_SECRET=your-supabase-jwt-secret-here
export JWT_SECRET=your-jwt-secret-here

# Super Admin Credentials (Replace with your actual credentials)
export SUPER_ADMIN_EMAIL=your-admin-email@example.com
export SUPER_ADMIN_PASSWORD=your-secure-password-here

# SMTP Configuration (Replace with your actual SMTP credentials)
export SMTP_SERVER=your-smtp-server.com
export SMTP_PORT=587
export SMTP_USERNAME=your-smtp-username@example.com
export SMTP_PASSWORD=your-smtp-password-here
export FROM_EMAIL=your-from-email@example.com
export FROM_NAME=Your App Name

# Supabase Configuration (Replace with your actual Supabase credentials)
export SUPABASE_URL=your-supabase-url-here
export SUPABASE_ANON_KEY=your-supabase-anon-key-here

# AI API Keys (Replace with your actual keys)
export GOOGLE_API_KEY=your-google-api-key-here
export OPENAI_API_KEY=your-openai-api-key-here

# Encryption Key (Replace with your actual encryption key)
export ENCRYPTION_KEY=your-encryption-key-here

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