#!/bin/bash

# ClinicHub Quick Setup Script
# For Alpine Linux Docker Container

set -e

echo "🏥 ClinicHub Quick Setup Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available"
    exit 1
fi

# Use docker compose or docker-compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

print_status "Using: $DOCKER_COMPOSE"

# Stop any existing services
print_status "Stopping existing services..."
$DOCKER_COMPOSE down

# Remove old volumes if requested
read -p "Reset database and start fresh? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Removing all data volumes..."
    $DOCKER_COMPOSE down -v
    docker system prune -f
fi

# Start services
print_status "Starting ClinicHub services..."
$DOCKER_COMPOSE up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check service status
print_status "Checking service status..."
$DOCKER_COMPOSE ps

# Wait for backend to be ready
print_status "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8001/health &>/dev/null; then
        print_status "Backend is ready!"
        break
    fi
    echo -n "."
    sleep 2
done

# Initialize admin user
print_status "Initializing admin user..."
curl -X POST "http://localhost:8001/api/auth/init-admin" || print_warning "Admin user may already exist"

# Test login
print_status "Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    print_status "✅ Login test successful!"
else
    print_warning "⚠️  Login test failed, but system may still work"
fi

# Final status
echo
echo "=================================================="
print_status "🎉 ClinicHub Setup Complete!"
echo "=================================================="
echo
print_status "Access your system:"
print_status "  📱 Frontend Dashboard: http://localhost:3000"
print_status "  🔧 Backend API: http://localhost:8001/docs"
print_status "  🗄️  Database: MongoDB on port 27017"
echo
print_status "Default credentials:"
print_status "  Username: admin"
print_status "  Password: admin123"
echo
print_status "Useful commands:"
print_status "  View logs: $DOCKER_COMPOSE logs"
print_status "  Restart: $DOCKER_COMPOSE restart"
print_status "  Stop: $DOCKER_COMPOSE down"
echo
print_status "System is ready! 🚀"