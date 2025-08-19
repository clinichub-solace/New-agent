#!/bin/bash
echo "🏥 ClinicHub Alpine Deployment"
echo "=============================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Create data directories
mkdir -p data/mongodb data/backend/logs

# Build and start
echo "📦 Building containers..."
docker-compose build

echo "🚀 Starting ClinicHub..."
docker-compose up -d

echo "⏳ Waiting for services..."
sleep 30

echo "🏥 ClinicHub deployed successfully!"
echo ""
echo "Access URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8001"
echo "  Login:    admin / admin123"
echo ""
echo "Management:"
echo "  Stop:     docker-compose down"
echo "  Logs:     docker-compose logs"
echo "  Restart:  docker-compose restart"
