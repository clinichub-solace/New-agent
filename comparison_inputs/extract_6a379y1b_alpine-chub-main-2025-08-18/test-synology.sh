#!/bin/bash
# ClinicHub Synology Integration Test Script

echo "🔧 ClinicHub - Synology Integration Test"
echo "======================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_test() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✅ PASS${NC} $1"
}

print_fail() {
    echo -e "${RED}❌ FAIL${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARN${NC} $1"
}

# Test 1: Check if running on Synology
print_test "Checking Synology environment..."
if [ -f "/etc.defaults/VERSION" ]; then
    print_pass "Running on Synology NAS"
    cat /etc.defaults/VERSION | grep -E "(productversion|buildnumber)"
else
    print_warning "Not running on Synology NAS (this is okay for development)"
fi

# Test 2: Check Docker availability
print_test "Checking Docker installation..."
if command -v docker &> /dev/null; then
    print_pass "Docker is available"
    docker --version
else
    print_fail "Docker not found. Install via Package Center."
    exit 1
fi

# Test 3: Check Docker Compose
print_test "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    print_pass "Docker Compose is available"
    docker-compose --version
else
    print_fail "Docker Compose not found."
    exit 1
fi

# Test 4: Check volume access
print_test "Checking volume access..."
if [ -d "/volume1" ]; then
    print_pass "Volume1 accessible"
    ls -la /volume1/ | head -5
else
    print_warning "Volume1 not found. Adjust paths in docker-compose.synology.yml"
fi

# Test 5: Check network connectivity
print_test "Checking network connectivity..."
if ping -c 1 google.com &> /dev/null; then
    print_pass "Internet connectivity available"
else
    print_fail "No internet connectivity"
fi

# Test 6: Test ClinicHub services (if running)
print_test "Checking ClinicHub services..."
if curl -s "http://localhost:8001/api/health" &> /dev/null; then
    print_pass "Backend is running"
    backend_status=$(curl -s "http://localhost:8001/api/health")
    echo "   Backend response: $backend_status"
else
    print_warning "Backend not running (start with docker-compose)"
fi

if curl -s "http://localhost:3000" &> /dev/null; then
    print_pass "Frontend is running"
else
    print_warning "Frontend not running (start with docker-compose)"
fi

# Test 7: Check Synology SSO configuration
print_test "Checking Synology SSO configuration..."
if [ -f "backend/.env" ]; then
    if grep -q "SYNOLOGY_DSM_URL" backend/.env; then
        print_pass "Synology DSM URL configured"
        grep "SYNOLOGY_DSM_URL" backend/.env
    else
        print_warning "Synology DSM URL not configured in backend/.env"
    fi
else
    print_warning "Backend .env file not found"
fi

# Test 8: Test Synology API access (if configured)
print_test "Testing Synology API access..."
if [ -f "synology_auth_test.py" ]; then
    python3 synology_auth_test.py 2>&1 | head -10
else
    print_warning "Synology auth test script not found"
fi

echo
echo "🎯 Test Summary"
echo "==============="
echo "✅ Run './deploy-synology.sh' for automated deployment"
echo "✅ Access ClinicHub at https://YOUR-NAS-IP:3000"
echo "✅ Default login: admin / admin123"
echo "✅ Configure Synology SSO in System Settings"

echo
echo "📝 Next Steps:"
echo "1. Update YOUR-NAS-IP in docker-compose.synology.yml"
echo "2. Run: docker-compose -f docker-compose.synology.yml up -d"
echo "3. Open https://YOUR-NAS-IP:3000 in browser"
echo "4. Test Synology SSO login"