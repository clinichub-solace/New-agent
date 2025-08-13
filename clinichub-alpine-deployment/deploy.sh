#!/bin/bash
# ClinicHub Alpine Docker Deployment Script
# This script deploys ClinicHub on Alpine-based Docker environments

set -e

echo "🏥 ClinicHub Alpine Docker Deployment"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are available"
}

# Check system requirements
check_requirements() {
    print_header "Checking system requirements..."
    
    # Check available disk space (minimum 2GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 2000000 ]; then
        print_warning "Low disk space detected. ClinicHub requires at least 2GB of free space."
    fi
    
    # Check if ports are available
    if netstat -tuln 2>/dev/null | grep -q ":80\s"; then
        print_warning "Port 80 is already in use. You may need to stop other web servers."
    fi
    
    if netstat -tuln 2>/dev/null | grep -q ":3000\s"; then
        print_warning "Port 3000 is already in use. You may need to stop other applications."
    fi
    
    if netstat -tuln 2>/dev/null | grep -q ":8001\s"; then
        print_warning "Port 8001 is already in use. You may need to stop other applications."
    fi
    
    print_status "System requirements check completed"
}

# Create necessary directories
setup_directories() {
    print_header "Setting up directories..."
    
    # Create data directories
    mkdir -p data/mongodb
    mkdir -p data/backend/logs
    mkdir -p nginx/ssl
    mkdir -p backups
    
    # Set appropriate permissions
    chmod -R 755 data/
    chmod -R 755 nginx/
    chmod -R 755 backups/
    
    print_status "Directory structure created"
}

# Generate SSL certificates (self-signed for development)
setup_ssl() {
    print_header "Setting up SSL certificates..."
    
    if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/privkey.pem ]; then
        print_status "Generating self-signed SSL certificates..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/privkey.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=ClinicHub/CN=localhost" 2>/dev/null || {
            print_warning "OpenSSL not available. SSL certificates not generated."
            print_warning "HTTPS will not be available until certificates are provided."
        }
    else
        print_status "SSL certificates already exist"
    fi
}

# Build and start containers
deploy_containers() {
    print_header "Building and starting ClinicHub containers..."
    
    # Pull base images first
    print_status "Pulling base Docker images..."
    docker-compose pull --quiet || print_warning "Failed to pull some images"
    
    # Build custom images
    print_status "Building ClinicHub images..."
    docker-compose build --no-cache
    
    # Start containers
    print_status "Starting ClinicHub services..."
    docker-compose up -d
    
    # Wait for services to start
    print_status "Waiting for services to initialize..."
    sleep 30
    
    # Check service health
    check_health
}

# Health check function
check_health() {
    print_header "Checking service health..."
    
    # Check MongoDB
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        print_status "MongoDB is healthy"
    else
        print_warning "MongoDB health check failed"
    fi
    
    # Check Backend
    if curl -f -s http://localhost:8001/api/health > /dev/null; then
        print_status "Backend is healthy"
    else
        print_warning "Backend health check failed"
    fi
    
    # Check Frontend
    if curl -f -s http://localhost:3000 > /dev/null; then
        print_status "Frontend is healthy"
    else
        print_warning "Frontend health check failed"
    fi
    
    # Check Nginx
    if curl -f -s http://localhost > /dev/null; then
        print_status "Nginx is healthy"
    else
        print_warning "Nginx health check failed"
    fi
}

# Initialize sample data
initialize_data() {
    print_header "Initializing sample data..."
    
    # Wait for MongoDB to be fully ready
    sleep 10
    
    # The init-mongo.js script should automatically run
    # Check if data was initialized
    if docker-compose exec -T mongodb mongosh clinichub --eval "db.patients.countDocuments({})" | grep -q "2"; then
        print_status "Sample data initialized successfully"
    else
        print_warning "Sample data initialization may have failed"
    fi
}

# Display completion message
show_completion() {
    echo
    echo -e "${GREEN}🎉 ClinicHub Deployment Complete!${NC}"
    echo "================================="
    echo
    print_status "Access URLs:"
    echo "  Frontend (via Nginx): http://localhost"
    echo "  Frontend (direct):    http://localhost:3000"
    echo "  Backend API:          http://localhost:8001"
    echo "  API Documentation:    http://localhost:8001/docs"
    echo
    print_status "Default Credentials:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo
    print_status "Docker Management:"
    echo "  View logs:      docker-compose logs [service]"
    echo "  Restart:        docker-compose restart [service]"
    echo "  Stop:           docker-compose down"
    echo "  Start:          docker-compose up -d"
    echo
    print_status "Data Locations:"
    echo "  MongoDB data:   ./data/mongodb/"
    echo "  Backend logs:   ./data/backend/logs/"
    echo "  Backups:        ./backups/"
    echo
    print_warning "Important Notes:"
    echo "- Change default admin password immediately"
    echo "- Configure proper SSL certificates for production"
    echo "- Set up regular backups for production use"
    echo "- Monitor disk space in ./data/ directory"
    echo
    echo -e "${BLUE}Happy practicing with ClinicHub! 🏥${NC}"
}

# Main execution
main() {
    print_header "Starting ClinicHub deployment..."
    
    check_docker
    check_requirements
    setup_directories
    setup_ssl
    deploy_containers
    initialize_data
    show_completion
}

# Run main function
main "$@"