#!/bin/bash
# ClinicHub Synology NAS Deployment Script
# This script sets up ClinicHub on Synology NAS with SSO integration

set -e

echo "🏥 ClinicHub - Synology NAS Deployment Script"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables
NAS_IP=""
NAS_HTTPS_PORT="5001"
VOLUME_NAME="volume1"
ADMIN_USER=""
SETUP_SSL="false"

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

# Function to check if running on Synology
check_synology() {
    if [ ! -f "/etc.defaults/VERSION" ]; then
        print_error "This script should be run on a Synology NAS system."
        print_warning "If you're running this on a different system, please modify the paths accordingly."
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "Synology system detected!"
        cat /etc.defaults/VERSION | grep -E "(productversion|buildnumber)"
    fi
}

# Function to get configuration from user
get_configuration() {
    echo
    echo "📝 Configuration Setup"
    echo "====================="
    
    # Get NAS IP address
    read -p "Enter your Synology NAS IP address: " NAS_IP
    if [ -z "$NAS_IP" ]; then
        print_error "NAS IP address is required!"
        exit 1
    fi
    
    # Get volume name (default: volume1)
    read -p "Enter your Synology volume name [volume1]: " input_volume
    VOLUME_NAME=${input_volume:-volume1}
    
    # Get admin user
    read -p "Enter your DSM admin username: " ADMIN_USER
    if [ -z "$ADMIN_USER" ]; then
        print_error "Admin username is required for SSO setup!"
        exit 1
    fi
    
    # SSL setup
    read -p "Do you have SSL certificates configured in DSM? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SETUP_SSL="true"
    fi
    
    print_status "Configuration collected:"
    print_status "  NAS IP: $NAS_IP"
    print_status "  Volume: /$VOLUME_NAME"
    print_status "  Admin User: $ADMIN_USER"
    print_status "  SSL Enabled: $SETUP_SSL"
    echo
}

# Function to create directory structure
setup_directories() {
    print_status "Setting up directory structure..."
    
    BASE_DIR="/$VOLUME_NAME/docker/clinichub"
    
    # Create directories
    sudo mkdir -p "$BASE_DIR/mongodb"
    sudo mkdir -p "$BASE_DIR/backend/logs"
    sudo mkdir -p "$BASE_DIR/nginx/ssl"
    sudo mkdir -p "$BASE_DIR/backups"
    
    # Set permissions
    sudo chown -R root:root "$BASE_DIR"
    sudo chmod -R 755 "$BASE_DIR"
    
    print_status "Directory structure created at $BASE_DIR"
}

# Function to configure environment variables
setup_environment() {
    print_status "Configuring environment variables..."
    
    # Update docker-compose.synology.yml with actual values
    sed -i "s/YOUR-NAS-IP/$NAS_IP/g" docker-compose.synology.yml
    sed -i "s/YOUR-CERT/clinichub/g" docker-compose.synology.yml
    
    # Update nginx config
    sed -i "s/YOUR-NAS-IP/$NAS_IP/g" nginx/clinichub.conf
    
    # Create environment file for backend
    cat > backend/.env << EOF
MONGO_URL=mongodb://admin:ClinicHub2024!Secure@mongodb:27017/clinichub?authSource=admin
SECRET_KEY=clinichub-super-secure-secret-key-2024
JWT_SECRET_KEY=clinichub-jwt-secret-key-2024-very-secure
DEBUG=false
HOST=0.0.0.0
PORT=8001

# Synology DSM Integration
SYNOLOGY_DSM_URL=https://$NAS_IP:$NAS_HTTPS_PORT
SYNOLOGY_VERIFY_SSL=$SETUP_SSL
SYNOLOGY_SESSION_NAME=ClinicHub

# Timezone
TZ=America/New_York
EOF

    # Create environment file for frontend
    cat > frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$NAS_IP:8001
NODE_ENV=production
EOF
    
    print_status "Environment configured!"
}

# Function to setup SSL certificates
setup_ssl() {
    if [ "$SETUP_SSL" = "true" ]; then
        print_status "Setting up SSL certificates..."
        
        print_warning "Manual step required:"
        echo "1. Go to DSM Control Panel > Security > Certificate"
        echo "2. Create or import a certificate for ClinicHub"
        echo "3. Note the certificate directory path"
        echo "4. Update the nginx configuration with the correct certificate paths"
        echo
        read -p "Press Enter when SSL certificates are configured..."
    fi
}

# Function to install Docker (if not present)
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. Please install Docker via Synology Package Center."
        echo "1. Open Package Center in DSM"
        echo "2. Search for 'Docker' and install it"
        echo "3. Enable SSH and run this script again"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose not found. Installing..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    print_status "Docker and Docker Compose are available!"
}

# Function to deploy ClinicHub
deploy_clinichub() {
    print_status "Deploying ClinicHub containers..."
    
    # Build and start containers
    docker-compose -f docker-compose.synology.yml build
    docker-compose -f docker-compose.synology.yml up -d
    
    # Wait for services to start
    print_status "Waiting for services to initialize..."
    sleep 30
    
    # Check service health
    if curl -f -s "http://localhost:8001/api/health" > /dev/null; then
        print_status "Backend is healthy!"
    else
        print_warning "Backend health check failed. Check logs: docker-compose -f docker-compose.synology.yml logs backend"
    fi
    
    if curl -f -s "http://localhost:3000" > /dev/null; then
        print_status "Frontend is healthy!"
    else
        print_warning "Frontend health check failed. Check logs: docker-compose -f docker-compose.synology.yml logs frontend"
    fi
}

# Function to test Synology SSO
test_sso() {
    print_status "Testing Synology SSO integration..."
    
    # Run the Synology auth test
    if [ -f "synology_auth_test.py" ]; then
        python3 synology_auth_test.py
    else
        print_warning "Synology auth test not found. SSO testing skipped."
    fi
}

# Function to display final instructions
show_completion() {
    echo
    echo "🎉 ClinicHub Deployment Complete!"
    echo "================================="
    echo
    print_status "Access URLs:"
    echo "  Frontend: https://$NAS_IP:3000"
    echo "  Backend API: https://$NAS_IP:8001"
    echo "  Admin Login: admin / admin123"
    echo
    print_status "Next Steps:"
    echo "1. Open https://$NAS_IP:3000 in your browser"
    echo "2. Login with admin/admin123 initially"
    echo "3. Go to System Settings to configure Synology SSO"
    echo "4. Test SSO login with your DSM username: $ADMIN_USER"
    echo "5. Create additional users and assign roles"
    echo
    print_status "Management Commands:"
    echo "  Start:   docker-compose -f docker-compose.synology.yml up -d"
    echo "  Stop:    docker-compose -f docker-compose.synology.yml down"
    echo "  Logs:    docker-compose -f docker-compose.synology.yml logs [service]"
    echo "  Update:  docker-compose -f docker-compose.synology.yml pull && docker-compose -f docker-compose.synology.yml up -d"
    echo
    print_warning "Security Reminders:"
    echo "- Change default admin password immediately"
    echo "- Configure firewall rules to restrict access"
    echo "- Enable two-factor authentication in DSM"
    echo "- Regular backups are stored in: /$VOLUME_NAME/docker/clinichub/backups"
}

# Main execution
main() {
    check_synology
    get_configuration
    setup_directories
    check_docker
    setup_environment
    setup_ssl
    deploy_clinichub
    test_sso
    show_completion
}

# Run the main function
main "$@"