#!/bin/bash

# ClinicHub Communication Infrastructure Deployment Script
# Phase 2B: Email, Fax, and VoIP Services
# Designed for Synology NAS deployment

set -e

echo "🏥 ClinicHub Communication Infrastructure Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${DOMAIN:-clinic.local}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@clinic.local}"
COMPOSE_FILE="docker-compose.communication.yml"

echo -e "${BLUE}Configuration:${NC}"
echo "Domain: $DOMAIN"
echo "Admin Email: $ADMIN_EMAIL"
echo "Compose File: $COMPOSE_FILE"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

# Check if we're in the right directory
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ $COMPOSE_FILE not found in current directory${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Compose file found${NC}"

# Create necessary directories
echo -e "${BLUE}Creating directory structure...${NC}"
mkdir -p {mailu,gateway,certs,data}/{logs,config,data}
echo -e "${GREEN}✅ Directories created${NC}"

# Update Mailu configuration with user-provided values
echo -e "${BLUE}Configuring Mailu...${NC}"
sed -i "s/DOMAIN=clinic.local/DOMAIN=$DOMAIN/g" mailu/mailu.env
sed -i "s/admin@clinic.local/$ADMIN_EMAIL/g" mailu/mailu.env
echo -e "${GREEN}✅ Mailu configured${NC}"

# Pull Docker images
echo -e "${BLUE}Pulling Docker images...${NC}"
docker-compose -f $COMPOSE_FILE pull
echo -e "${GREEN}✅ Images pulled${NC}"

# Generate secrets
echo -e "${BLUE}Generating secrets...${NC}"
MAILU_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)
sed -i "s/ClinicHub2025EmailSecretKey16Bytes/$MAILU_SECRET/g" mailu/mailu.env
echo -e "${GREEN}✅ Secrets generated${NC}"

# Start the services
echo -e "${BLUE}Starting communication services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

echo -e "${GREEN}✅ Services started successfully!${NC}"
echo ""

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to initialize...${NC}"
sleep 30

# Check service health
echo -e "${BLUE}Checking service health...${NC}"

# Check Mailu
if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Mailu is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Mailu may still be starting up${NC}"
fi

# Check Communication Gateway
if curl -f -s http://localhost:8100/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Communication Gateway is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Communication Gateway may still be starting up${NC}"
fi

echo ""
echo -e "${GREEN}🎉 ClinicHub Communication Infrastructure Deployed!${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "• Mailu Admin: http://localhost:8080/admin"
echo "• Mailu Webmail: http://localhost:8080/webmail"
echo "• Communication Gateway API: http://localhost:8100"
echo "• Gateway Status: http://localhost:8100/status"
echo ""
echo -e "${BLUE}Default Credentials:${NC}"
echo "• Admin Email: $ADMIN_EMAIL"
echo "• Password: Set up through Mailu admin interface"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Access Mailu admin interface to set up email accounts"
echo "2. Configure DNS records for your domain:"
echo "   - MX record pointing to your server"
echo "   - SPF, DKIM, DMARC records for email security"
echo "3. Update ClinicHub backend to use communication gateway:"
echo "   COMMUNICATION_GATEWAY_URL=http://localhost:8100"
echo "4. Test email sending through the gateway API"
echo ""
echo -e "${YELLOW}For Synology NAS deployment:${NC}"
echo "1. Copy this entire infrastructure/ directory to your NAS"
echo "2. Install Docker from Package Center"
echo "3. SSH into your NAS and run this script"
echo "4. Configure reverse proxy in DSM for web access"
echo ""
echo -e "${BLUE}Logs and Monitoring:${NC}"
echo "• View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "• Stop services: docker-compose -f $COMPOSE_FILE down"
echo "• Restart services: docker-compose -f $COMPOSE_FILE restart"