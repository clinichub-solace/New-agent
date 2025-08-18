#!/bin/bash

# ClinicHub Production Deployment Script
# Deploys a production-ready ClinicHub with security hardening, monitoring, and backup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check OpenSSL
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Generate secrets if they don't exist
generate_secrets() {
    log_info "Generating secrets..."
    
    mkdir -p secrets
    chmod 700 secrets
    
    # Generate secrets if they don't exist
    secrets=(
        "mongo_root_password"
        "mongo_connection_string"
        "app_secret_key"
        "jwt_secret_key"
        "postgres_fhir_password"
        "rabbitmq_password"
        "mirth_admin_password"
        "grafana_admin_password"
        "minio_root_password"
        "restic_password"
    )
    
    for secret in "${secrets[@]}"; do
        if [[ ! -f "secrets/$secret" ]]; then
            openssl rand -base64 32 > "secrets/$secret"
            chmod 600 "secrets/$secret"
            log_info "Generated secret: $secret"
        fi
    done
    
    # Generate MongoDB connection string
    if [[ ! -f "secrets/mongo_connection_string" ]]; then
        MONGO_PASS=$(cat secrets/mongo_root_password | tr -d '\n')
        echo "mongodb://admin:${MONGO_PASS}@mongodb:27017/clinichub?authSource=admin" > secrets/mongo_connection_string
        chmod 600 secrets/mongo_connection_string
        log_info "Generated MongoDB connection string"
    fi
    
    log_success "Secrets generation completed"
}

# Create network
create_network() {
    log_info "Creating Docker network..."
    
    if ! docker network ls | grep -q "clinichub-network"; then
        docker network create clinichub-network
        log_success "Created clinichub-network"
    else
        log_info "Network clinichub-network already exists"
    fi
}

# Deploy core services
deploy_core() {
    log_info "Deploying core ClinicHub services..."
    
    docker-compose down --remove-orphans
    docker-compose build --no-cache
    docker-compose up -d
    
    log_success "Core services deployed"
}

# Deploy interoperability services
deploy_interop() {
    log_info "Deploying interoperability services..."
    
    docker-compose -f docker-compose.interop.yml down --remove-orphans
    docker-compose -f docker-compose.interop.yml build --no-cache
    docker-compose -f docker-compose.interop.yml up -d
    
    log_success "Interoperability services deployed"
}

# Deploy monitoring services
deploy_monitoring() {
    log_info "Deploying monitoring services..."
    
    docker-compose -f docker-compose.monitoring.yml down --remove-orphans
    docker-compose -f docker-compose.monitoring.yml up -d
    
    log_success "Monitoring services deployed"
}

# Deploy backup services
deploy_backup() {
    log_info "Deploying backup services..."
    
    docker-compose -f docker-compose.backup.yml down --remove-orphans
    docker-compose -f docker-compose.backup.yml build --no-cache
    docker-compose -f docker-compose.backup.yml up -d
    
    log_success "Backup services deployed"
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for backend
    for i in {1..30}; do
        if curl -f http://localhost:8001/health &>/dev/null; then
            log_success "Backend is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Backend failed to start"
            exit 1
        fi
        sleep 10
    done
    
    # Wait for frontend
    for i in {1..30}; do
        if curl -f http://localhost:3000 &>/dev/null; then
            log_success "Frontend is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Frontend failed to start"
            exit 1
        fi
        sleep 10
    done
}

# Display deployment information
show_deployment_info() {
    log_success "ClinicHub Production Deployment Completed!"
    echo
    echo "🏥 DeplosyHub Access URLs:"
    echo "   Frontend:      http://localhost:3000"
    echo "   Backend API:   http://localhost:8001"
    echo
    echo "🔧 Monitoring & Management:"
    echo "   Grafana:       http://localhost:3001 (admin/$(cat secrets/grafana_admin_password))"
    echo "   Prometheus:    http://localhost:9090"
    echo "   Wazuh:         http://localhost:5601"
    echo "   HAPI FHIR:     http://localhost:8082/fhir"
    echo "   Mirth Connect: https://localhost:8443"
    echo "   MinIO:         http://localhost:9001 (clinichub/$(cat secrets/minio_root_password))"
    echo
    echo "🔒 Security Features Enabled:"
    echo "   ✅ Secrets managed via Docker secrets"
    echo "   ✅ MongoDB authentication and encryption"
    echo "   ✅ Non-root container users"
    echo "   ✅ HIPAA audit logging"
    echo "   ✅ Security monitoring (Wazuh)"
    echo "   ✅ Encrypted backups"
    echo
    echo "📊 Healthcare Interoperability:"
    echo "   ✅ FHIR R4 server (HAPI FHIR)"
    echo "   ✅ HL7 interface engine (Mirth Connect)"
    echo "   ✅ Event-driven architecture"
    echo "   ✅ Domain event publishing"
    echo
    echo "💾 Backup & Recovery:"
    echo "   ✅ Automated daily backups"
    echo "   ✅ Object storage (MinIO)"
    echo "   ✅ Encrypted backup repository (Restic)"
    echo "   ✅ 30-day retention policy"
    echo
    log_info "Login with: admin / admin123"
    log_warning "Change default passwords immediately in production!"
}

# Main deployment function
main() {
    echo "🏥 ClinicHub Production Deployment"
    echo "=================================="
    echo
    
    check_root
    check_prerequisites
    generate_secrets
    create_network
    deploy_core
    deploy_interop
    deploy_monitoring
    deploy_backup
    wait_for_services
    show_deployment_info
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"