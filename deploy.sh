#!/bin/bash

# Deployment script for Legatoo Backend
# This script should be run on the Hostinger server

set -e

echo "🚀 Starting Legatoo Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to the backend directory
cd /home/$USER/legatoo-app/legatoo_backend || {
    print_error "Backend directory not found. Please ensure the code is cloned to /home/$USER/legatoo-app/legatoo_backend"
    exit 1
}

print_status "Found backend directory"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    print_warning ".env.production not found. Creating from example..."
    if [ -f "env.production.example" ]; then
        cp env.production.example .env.production
        print_warning "Please update .env.production with your production values"
    else
        print_error "env.production.example not found. Please create .env.production manually"
        exit 1
    fi
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down || true

# Pull latest changes (if this is a git repository)
if [ -d "../.git" ]; then
    print_status "Pulling latest changes..."
    cd .. && git pull origin master && cd legatoo_backend || true
fi

# Build and start the application
print_status "Building and starting the application..."
docker-compose up -d --build

# Wait for the service to be ready
print_status "Waiting for service to be ready..."
sleep 15

# Health check
print_status "Performing health check..."
if curl -f http://localhost:8000/health; then
    print_status "✅ Backend is healthy and running!"
    print_status "🌐 Backend is available at: http://localhost:8000"
    print_status "📚 API Documentation: http://localhost:8000/docs"
else
    print_error "❌ Health check failed. Check the logs:"
    docker-compose logs backend
    exit 1
fi

# Show running containers
print_status "Running containers:"
docker-compose ps

print_status "🎉 Deployment completed successfully!"
