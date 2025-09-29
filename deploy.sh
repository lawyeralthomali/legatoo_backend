#!/bin/bash

# FastAPI Backend Deployment Script
# Lightweight deployment script for production environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🚀 Starting FastAPI Backend Deployment..."
echo "📅 Deployment Time: $(date)"
echo "=" * 60

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please run this script from the project root directory."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and wheel
print_status "Upgrading pip and wheel..."
pip install --upgrade pip setuptools wheel

# Install/Update dependencies
print_status "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Optional: Update code from git if repository exists
if [ -d ".git" ]; then
    print_status "Updating code from git repository..."
    git pull origin main || print_warning "Git pull failed, continuing with current code"
else
    print_status "No git repository found, skipping git pull"
fi

# Stop existing backend process
print_status "Stopping existing backend processes..."
pkill -f uvicorn || print_warning "No existing uvicorn process found"

# Wait for process to stop
sleep 2

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the backend application
print_status "Starting FastAPI application..."
print_status "Application will run in background with logs written to logs/app.log"

# Start uvicorn in background
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file .env.production > logs/app.log 2>&1 &

# Save the process ID
APP_PID=$!
echo $APP_PID > app.pid

print_success "Application started with PID: $APP_PID"
print_success "Application is running on port 8000"

# Wait a moment and check if the app is running
sleep 3
if ps -p $APP_PID > /dev/null; then
    print_success "✅ Application is running successfully!"
    print_status "📋 Logs: tail -f logs/app.log"
    print_status "🔍 Health check: curl http://localhost:8000/health"
    print_status "📚 API docs: http://localhost:8000/docs"
else
    print_error "❌ Application failed to start. Check logs/app.log for details."
    print_status "Last 20 lines of logs:"
    tail -20 logs/app.log
    exit 1
fi

echo "=" * 60
print_success "🎉 Deployment completed successfully!"
print_status "To stop the application: kill \$(cat app.pid)"
print_status "To view logs: tail -f logs/app.log"
print_status "To restart: ./deploy.sh"
echo "=" * 60