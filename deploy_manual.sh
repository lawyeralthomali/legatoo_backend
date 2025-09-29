#!/bin/bash

# Manual Deployment Script for Hostinger Server
# Run this script directly on your Hostinger server

set -e  # Exit on any error

echo "🚀 Starting manual deployment on Hostinger..."

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

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found! Please run this script from your project root directory."
    exit 1
fi

# Kill any existing processes
print_status "Stopping existing processes..."
pkill -f "exact_routes_backend.py" || true
pkill -f "deploy_backend.py" || true
pkill -f "run_fastapi.py" || true
pkill -f "uvicorn" || true

# Check available Python versions and use the best one
print_status "Checking available Python versions..."
PYTHON_BIN=""

# Try different Python versions in order of preference
for version in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
    if command -v $version &> /dev/null; then
        PYTHON_BIN=$version
        print_success "Found Python: $version"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    print_error "No Python installation found!"
    exit 1
fi

# Check Python version
print_status "Using Python: $PYTHON_BIN"
$PYTHON_BIN --version

# Install Python dependencies
print_status "Installing Python dependencies..."
$PYTHON_BIN -m pip install --upgrade pip setuptools wheel
$PYTHON_BIN -m pip install --user -r requirements.txt

# Verify installation
print_status "Verifying installation..."
$PYTHON_BIN -c "import fastapi, uvicorn, sqlalchemy, aiofiles; print('All dependencies installed successfully!')"

# Check if environment file exists
if [ ! -f "supabase.env" ]; then
    print_warning "supabase.env file not found!"
    print_warning "Please create supabase.env file with your environment variables."
    print_warning "You can copy from supabase.env.template"
fi

# Start the application
print_status "Starting FastAPI application..."
print_status "The app will run in the background. Check logs with: tail -f logs/app.log"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the application in background
nohup $PYTHON_BIN -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/app.log 2>&1 &

# Get the process ID
APP_PID=$!
echo $APP_PID > app.pid

print_success "Application started with PID: $APP_PID"
print_success "Application is running on port 8000"
print_success "Logs are being written to: logs/app.log"

# Wait a moment and check if the app is running
sleep 3
if ps -p $APP_PID > /dev/null; then
    print_success "✅ Application is running successfully!"
    print_status "You can check the health endpoint: curl http://localhost:8000/health"
else
    print_error "❌ Application failed to start. Check logs/app.log for details."
    exit 1
fi

print_success "🎉 Deployment completed successfully!"
print_status "To stop the application: kill \$(cat app.pid)"
print_status "To view logs: tail -f logs/app.log"
print_status "To restart: ./deploy_manual.sh"
