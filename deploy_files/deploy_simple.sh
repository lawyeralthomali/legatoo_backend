#!/bin/bash

# Simplified FastAPI Deployment Script for Hostinger VPS
# This script focuses on getting Python 3.8+ working

set -e

echo "🚀 Starting FastAPI Backend Deployment..."
echo "📅 Deployment Time: $(date)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Stop old processes
print_status "Stopping old backend processes..."
pkill -f "uvicorn" || true
pkill -f "python.*app.main" || true

# Try to install Python 3.8+ using deadsnakes PPA
print_status "Attempting to install Python 3.8+..."

if command -v apt &> /dev/null; then
    print_status "Using apt package manager..."
    
    # Update package list
    apt update -y
    
    # Install software-properties-common if not present
    apt install -y software-properties-common
    
    # Add deadsnakes PPA for newer Python versions
    add-apt-repository -y ppa:deadsnakes/ppa
    apt update -y
    
    # Try to install Python 3.8, 3.9, 3.10, 3.11, or 3.12
    for version in 3.12 3.11 3.10 3.9 3.8; do
        if apt install -y python${version} python${version}-venv python${version}-dev python${version}-pip; then
            PYTHON_BIN=python${version}
            print_success "Successfully installed Python ${version}"
            break
        else
            print_warning "Failed to install Python ${version}, trying next version..."
        fi
    done
    
    # Install essential build tools
    apt install -y build-essential git curl wget
    
elif command -v yum &> /dev/null; then
    print_status "Using yum package manager..."
    yum update -y
    yum install -y python38 python38-pip python38-devel gcc gcc-c++ make git curl wget
    PYTHON_BIN=python3.8
    
elif command -v dnf &> /dev/null; then
    print_status "Using dnf package manager..."
    dnf update -y
    dnf install -y python38 python38-pip python38-devel gcc gcc-c++ make git curl wget
    PYTHON_BIN=python3.8
    
else
    print_error "No supported package manager found!"
    exit 1
fi

# Check if we got a suitable Python version
if [ -z "$PYTHON_BIN" ]; then
    print_error "Failed to install Python 3.8+"
    exit 1
fi

print_status "Using Python: $PYTHON_BIN"
$PYTHON_BIN --version

# Create virtual environment
print_status "Creating virtual environment..."
$PYTHON_BIN -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Verify installation
print_status "Verifying installation..."
python -c "import fastapi, uvicorn, sqlalchemy; print('✅ All dependencies installed successfully!')"

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs

# Start the application
print_status "Starting FastAPI application..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/app.log 2>&1 &

# Get the process ID
APP_PID=$!
echo $APP_PID > app.pid

print_success "Application started with PID: $APP_PID"
print_success "Application is running on port 8000"

# Wait and check if app is running
sleep 3
if ps -p $APP_PID > /dev/null; then
    print_success "✅ Application is running successfully!"
    print_status "Health check: curl http://localhost:8000/health"
else
    print_error "❌ Application failed to start. Check logs/app.log"
    exit 1
fi

print_success "🎉 Deployment completed successfully!"
print_status "To stop: kill \$(cat app.pid)"
print_status "To view logs: tail -f logs/app.log"
