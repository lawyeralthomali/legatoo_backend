#!/bin/bash

# FastAPI Backend Production Deployment Script for Hostinger VPS
# This script works without sudo since we're running as root

set -e  # Exit on any error

echo "🚀 Starting FastAPI Backend Production Deployment..."
echo "📅 Deployment Time: $(date)"

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

# Stop old backend processes
print_status "Stopping old backend processes..."
pkill -f "exact_routes_backend.py" || true
pkill -f "deploy_backend.py" || true
pkill -f "run_fastapi.py" || true
pkill -f "uvicorn" || true

# Check available Python versions and use the best one
print_status "Detecting best available Python version..."
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
    print_error "No suitable Python version found (>= 3.8 required)!"
    print_status "Installing Python 3.12 via deadsnakes PPA..."
    
    # Update apt repositories (no sudo needed as root)
    print_status "Updating apt repositories..."
    apt update -y
    
    # Install Python 3.12 (no sudo needed as root)
    print_status "Installing Python 3.12..."
    apt install -y software-properties-common
    add-apt-repository -y ppa:deadsnakes/ppa
    apt update -y
    apt install -y python3.12 python3.12-venv python3.12-dev
    
    PYTHON_BIN=python3.12
    print_success "Python 3.12 installed successfully"
fi

# Check Python version
print_status "Using Python: $PYTHON_BIN"
$PYTHON_BIN --version

# Install essential tools
print_status "Installing essential tools..."
apt install -y python3-dev python3-pip build-essential git curl wget unzip

# Create virtual environment
print_status "Creating virtual environment..."
$PYTHON_BIN -m venv venv

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Rust compiler for tiktoken
print_status "Installing Rust compiler..."
apt install -y rustc

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install uvicorn
pip install tiktoken
pip install fastapi sqlalchemy aiofiles

# Install remaining dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    print_status "Installing from requirements.txt..."
    pip install -r requirements.txt
fi

# Verify installation
print_status "Verifying installation..."
python -c "import fastapi, uvicorn, sqlalchemy, aiofiles; print('All dependencies installed successfully!')"

# Configure firewall
print_status "Configuring firewall..."
apt install -y ufw
ufw allow ssh
ufw allow 8000
ufw --force enable

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs

# Start the application
print_status "Starting FastAPI application..."
print_status "The app will run in the background. Check logs with: tail -f logs/app.log"

# Start the application in background
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/app.log 2>&1 &

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
print_status "To restart: ./deploy_files/deploy_production.sh"
