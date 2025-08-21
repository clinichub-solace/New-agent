#!/bin/bash
# ClinicHub Production Build Script for Proxmox Deployment

set -e

echo "🏥 ClinicHub Production Build Script"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found. Run this script from the proxmox-deployment directory.${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your configuration before continuing.${NC}"
    echo -e "${YELLOW}   At minimum, set: DOMAIN, MONGO_ROOT_PASSWORD, SECRET_KEY, JWT_SECRET_KEY${NC}"
    exit 1
fi

# Source environment variables
source .env

# Validate required variables
if [ -z "$DOMAIN" ] || [ -z "$MONGO_ROOT_PASSWORD" ] || [ -z "$SECRET_KEY" ] || [ -z "$JWT_SECRET_KEY" ]; then
    echo -e "${RED}❌ Error: Missing required environment variables in .env file${NC}"
    echo "   Required: DOMAIN, MONGO_ROOT_PASSWORD, SECRET_KEY, JWT_SECRET_KEY"
    exit 1
fi

echo -e "${GREEN}✅ Environment configuration validated${NC}"

# Build backend Docker image
echo "🐳 Building backend Docker image..."
if [ -d "../backend" ]; then
    # Copy backend files to build context
    cp -r ../backend ./
    docker build -f Dockerfile.backend -t clinichub-backend:latest .
    rm -rf ./backend
    echo -e "${GREEN}✅ Backend image built successfully${NC}"
else
    echo -e "${RED}❌ Error: Backend directory not found at ../backend${NC}"
    exit 1
fi

# Build frontend production assets
echo "⚛️  Building frontend production assets..."
if [ -d "../frontend" ]; then
    cd ../frontend
    
    # Ensure production environment is set
    export NODE_ENV=production
    export REACT_APP_BACKEND_URL=/api
    
    # Install dependencies and build
    if command -v yarn &> /dev/null; then
        yarn install --frozen-lockfile
        yarn build
    else
        npm ci
        npm run build
    fi
    
    # Copy build to deployment directory
    cd ../proxmox-deployment
    rm -rf frontend
    mkdir -p frontend
    cp -r ../frontend/build ./frontend/
    echo -e "${GREEN}✅ Frontend assets built successfully${NC}"
else
    echo -e "${RED}❌ Error: Frontend directory not found at ../frontend${NC}"
    exit 1
fi

# Generate secrets if they're defaults
if [ "$SECRET_KEY" = "your_super_secure_secret_key_here_64_chars_minimum" ]; then
    echo -e "${YELLOW}⚠️  Generating new SECRET_KEY...${NC}"
    NEW_SECRET=$(openssl rand -hex 32)
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
fi

if [ "$JWT_SECRET_KEY" = "your_jwt_secret_key_here_32_chars_minimum" ]; then
    echo -e "${YELLOW}⚠️  Generating new JWT_SECRET_KEY...${NC}"
    NEW_JWT_SECRET=$(openssl rand -hex 16)
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_JWT_SECRET/" .env
fi

echo ""
echo -e "${GREEN}🎉 Build completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Ensure DNS points to your server: $DOMAIN"
echo "3. Configure firewall to allow ports 80 and 443"
echo "4. Run: docker compose up -d"
echo "5. Verify: curl -i https://$DOMAIN/api/health"
echo ""
echo -e "${GREEN}ClinicHub will be available at: https://$DOMAIN${NC}"