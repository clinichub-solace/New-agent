#!/bin/bash

# ClinicHub Installation Script
# Supports Ubuntu/Debian and CentOS/RHEL/Fedora

set -e

echo "=============================================="
echo "🏥 ClinicHub Installation Script"
echo "=============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    else
        print_error "Cannot detect operating system"
        exit 1
    fi
    
    print_status "Detected OS: $OS $VERSION"
}

# Install dependencies based on OS
install_dependencies() {
    print_status "Installing system dependencies..."
    
    if [[ $OS == *"Ubuntu"* ]] || [[ $OS == *"Debian"* ]]; then
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv nodejs npm mongodb git curl wget
        
        # Install Yarn
        curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
        echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
        sudo apt update && sudo apt install -y yarn
        
    elif [[ $OS == *"CentOS"* ]] || [[ $OS == *"Red Hat"* ]] || [[ $OS == *"Fedora"* ]]; then
        if command -v dnf &> /dev/null; then
            sudo dnf install -y python3 python3-pip nodejs npm mongodb-server git curl wget
        else
            sudo yum install -y python3 python3-pip nodejs npm mongodb-server git curl wget
        fi
        
        # Install Yarn
        curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo
        if command -v dnf &> /dev/null; then
            sudo dnf install -y yarn
        else
            sudo yum install -y yarn
        fi
    else
        print_error "Unsupported operating system: $OS"
        exit 1
    fi
    
    print_status "Dependencies installed successfully!"
}

# Setup MongoDB
setup_mongodb() {
    print_status "Setting up MongoDB..."
    
    # Start and enable MongoDB
    if systemctl is-active --quiet mongod; then
        print_warning "MongoDB is already running"
    else
        sudo systemctl start mongod
        sudo systemctl enable mongod
        print_status "MongoDB started and enabled"
    fi
}

# Clone repository
clone_repository() {
    print_status "Cloning ClinicHub repository..."
    
    if [[ -d "clinichub" ]]; then
        print_warning "ClinicHub directory already exists. Updating..."
        cd clinichub
        git pull
    else
        if [[ -z "$REPO_URL" ]]; then
            read -p "Enter GitHub repository URL: " REPO_URL
        fi
        git clone "$REPO_URL" clinichub
        cd clinichub
    fi
    
    print_status "Repository cloned/updated successfully!"
}

# Setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        print_status "Creating backend .env file..."
        cat > .env << EOF
# Database
MONGO_URL=mongodb://localhost:27017/clinichub

# Security
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# Application
DEBUG=True
HOST=0.0.0.0
PORT=8001
EOF
    fi
    
    cd ..
    print_status "Backend setup completed!"
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    cd frontend
    
    # Install Node.js dependencies
    yarn install
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        print_status "Creating frontend .env file..."
        cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001/api
REACT_APP_APP_NAME=ClinicHub
REACT_APP_VERSION=1.0.0
EOF
    fi
    
    cd ..
    print_status "Frontend setup completed!"
}

# Create systemd services
create_services() {
    print_status "Creating systemd services..."
    
    # Backend service
    sudo tee /etc/systemd/system/clinichub-backend.service > /dev/null << EOF
[Unit]
Description=ClinicHub Backend
After=network.target mongod.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)/backend
Environment=PATH=$(pwd)/backend/venv/bin
ExecStart=$(pwd)/backend/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    sudo tee /etc/systemd/system/clinichub-frontend.service > /dev/null << EOF
[Unit]
Description=ClinicHub Frontend
After=network.target clinichub-backend.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)/frontend
ExecStart=/usr/bin/yarn start
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    print_status "Systemd services created!"
}

# Start services
start_services() {
    print_status "Starting ClinicHub services..."
    
    # Enable and start services
    sudo systemctl enable clinichub-backend clinichub-frontend
    sudo systemctl start clinichub-backend
    sleep 5
    sudo systemctl start clinichub-frontend
    
    print_status "Services started!"
}

# Initialize demo data
init_demo_data() {
    print_status "Initializing demo data..."
    
    cd backend
    source venv/bin/activate
    
    # Wait for backend to be ready
    for i in {1..30}; do
        if curl -f http://localhost:8001/api/health &>/dev/null; then
            break
        fi
        echo "Waiting for backend to start... ($i/30)"
        sleep 2
    done
    
    # Initialize demo data
    python -c "
import requests
import json
import time

# Wait a bit more
time.sleep(5)

try:
    # Login and get token
    response = requests.post('http://localhost:8001/api/auth/login', 
        data={'username': 'admin', 'password': 'admin123'})
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # Initialize all demo data
    endpoints = [
        '/api/lab-tests/init',
        '/api/icd10/init', 
        '/api/erx/init',
        '/api/system/init-appointment-types',
        '/api/communications/init-templates',
        '/api/forms/templates/init-compliant'
    ]

    print('Initializing demo data...')
    for endpoint in endpoints:
        try:
            resp = requests.post(f'http://localhost:8001{endpoint}', headers=headers)
            print(f'{endpoint}: {resp.status_code}')
        except Exception as e:
            print(f'{endpoint}: Error - {e}')

    print('Demo data initialization completed!')
except Exception as e:
    print(f'Error initializing demo data: {e}')
"
    
    cd ..
    print_status "Demo data initialized!"
}

# Main installation function
main() {
    echo
    print_status "Starting ClinicHub installation..."
    echo
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        print_error "Please run as a regular user with sudo privileges"
        exit 1
    fi
    
    # Check for sudo privileges
    if ! sudo -n true 2>/dev/null; then
        print_error "This script requires sudo privileges"
        print_error "Please run: sudo -v"
        exit 1
    fi
    
    # Installation steps
    detect_os
    install_dependencies
    setup_mongodb
    clone_repository
    setup_backend
    setup_frontend
    
    # Ask if user wants to create systemd services
    echo
    read -p "Create systemd services for auto-start? (y/N): " create_services_choice
    if [[ $create_services_choice =~ ^[Yy]$ ]]; then
        create_services
        start_services
    else
        print_status "Skipping systemd services creation"
        print_status "To start manually:"
        print_status "  Backend: cd backend && source venv/bin/activate && python server.py"
        print_status "  Frontend: cd frontend && yarn start"
    fi
    
    # Ask if user wants to initialize demo data
    echo
    read -p "Initialize demo data? (Y/n): " init_demo_choice
    if [[ ! $init_demo_choice =~ ^[Nn]$ ]]; then
        init_demo_data
    fi
    
    echo
    echo "=============================================="
    print_status "🎉 ClinicHub installation completed!"
    echo "=============================================="
    echo
    print_status "Access ClinicHub at: http://localhost:3000"
    print_status "Default login: admin / admin123"
    echo
    print_status "Service status:"
    if systemctl is-active --quiet clinichub-backend; then
        print_status "  Backend: Running ✅"
    else
        print_warning "  Backend: Not running ⚠️"
    fi
    
    if systemctl is-active --quiet clinichub-frontend; then
        print_status "  Frontend: Running ✅"
    else
        print_warning "  Frontend: Not running ⚠️"
    fi
    
    if systemctl is-active --quiet mongod; then
        print_status "  MongoDB: Running ✅"
    else
        print_warning "  MongoDB: Not running ⚠️"
    fi
    echo
    print_status "For support, see: $(pwd)/INSTALLATION.md"
    echo
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "ClinicHub Installation Script"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --repo-url URL      Set GitHub repository URL"
        echo "  --no-demo          Skip demo data initialization"
        echo "  --no-services      Skip systemd services creation"
        echo
        exit 0
        ;;
    --repo-url)
        REPO_URL="$2"
        shift 2
        ;;
    --no-demo)
        SKIP_DEMO=true
        shift
        ;;
    --no-services)
        SKIP_SERVICES=true
        shift
        ;;
esac

# Run main installation
main "$@"