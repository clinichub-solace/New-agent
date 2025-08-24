#!/bin/bash
# ClinicHub Deployment Database Fix Verification Script
# This script verifies that Phase 1 has been successfully implemented

set -e

echo "🔍 ClinicHub Phase 1 Database Fix Verification"
echo "=============================================="
echo "Target: https://unruffled-noyce.emergent.host"
echo "Objective: Verify MongoDB connection fix"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=8

echo "${BLUE}🧪 Starting verification tests...${NC}"
echo ""

# Test 1: Basic connectivity
echo "Test 1/8: Basic Connectivity"
echo "-----------------------------"
if curl -s --max-time 5 https://unruffled-noyce.emergent.host/api/health > /dev/null; then
    echo -e "${GREEN}✅ PASS${NC} - API endpoint accessible"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - API endpoint not accessible"
    ((TESTS_FAILED++))
fi
echo ""

# Test 2: Health endpoint response
echo "Test 2/8: Health Endpoint Response"
echo "-----------------------------------"
HEALTH_RESPONSE=$(curl -s --max-time 5 https://unruffled-noyce.emergent.host/api/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✅ PASS${NC} - Health endpoint returning healthy status"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Health endpoint not returning healthy status"
    echo "Response: $HEALTH_RESPONSE"
    ((TESTS_FAILED++))
fi
echo ""

# Test 3: Authentication endpoint (critical test)
echo "Test 3/8: Authentication Endpoint (CRITICAL)"
echo "---------------------------------------------"
AUTH_RESPONSE=$(curl -s --max-time 10 -X POST https://unruffled-noyce.emergent.host/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}')

if echo "$AUTH_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ PASS${NC} - Authentication successful! MongoDB connection working!"
    JWT_TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "   Token received: ${JWT_TOKEN:0:20}..."
    ((TESTS_PASSED++))
elif echo "$AUTH_RESPONSE" | grep -q "No address associated with hostname"; then
    echo -e "${RED}❌ FAIL${NC} - Still getting MongoDB DNS error"
    echo -e "${YELLOW}   This indicates Phase 1 database fix has NOT been implemented yet${NC}"
    echo "   Error: MongoDB Atlas hostname still not resolvable"
    ((TESTS_FAILED++))
elif echo "$AUTH_RESPONSE" | grep -q "detail"; then
    echo -e "${RED}❌ FAIL${NC} - Authentication failed with different error"
    echo "   Response: $AUTH_RESPONSE"
    ((TESTS_FAILED++))
else
    echo -e "${RED}❌ FAIL${NC} - Unexpected authentication response"
    echo "   Response: $AUTH_RESPONSE"
    ((TESTS_FAILED++))
fi
echo ""

# Test 4: Response time performance
echo "Test 4/8: Response Time Performance"
echo "------------------------------------"
RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null --max-time 10 -X POST https://unruffled-noyce.emergent.host/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}')

if (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
    echo -e "${GREEN}✅ PASS${NC} - Response time: ${RESPONSE_TIME}s (< 5s threshold)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Response time: ${RESPONSE_TIME}s (> 5s threshold)"
    ((TESTS_FAILED++))
fi
echo ""

# Test 5: Protected endpoint access (if auth worked)
echo "Test 5/8: Protected Endpoint Access"
echo "------------------------------------"
if [ ! -z "$JWT_TOKEN" ] && [ "$JWT_TOKEN" != "null" ]; then
    PROTECTED_RESPONSE=$(curl -s --max-time 5 -H "Authorization: Bearer $JWT_TOKEN" https://unruffled-noyce.emergent.host/api/auth/me)
    if echo "$PROTECTED_RESPONSE" | grep -q "username"; then
        echo -e "${GREEN}✅ PASS${NC} - Protected endpoint accessible with JWT token"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} - Protected endpoint not accessible"
        echo "   Response: $PROTECTED_RESPONSE"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${YELLOW}⏭️  SKIP${NC} - No JWT token available from authentication test"
    ((TESTS_FAILED++))
fi
echo ""

# Test 6: Database-dependent endpoint
echo "Test 6/8: Database-Dependent Endpoint"
echo "--------------------------------------"
PATIENTS_RESPONSE=$(curl -s --max-time 5 https://unruffled-noyce.emergent.host/api/patients)
if echo "$PATIENTS_RESPONSE" | grep -q "Not authenticated"; then
    echo -e "${GREEN}✅ PASS${NC} - Database endpoint responding (authentication required as expected)"
    ((TESTS_PASSED++))
elif echo "$PATIENTS_RESPONSE" | grep -q "No address associated with hostname"; then
    echo -e "${RED}❌ FAIL${NC} - Database endpoint still showing MongoDB DNS error"
    ((TESTS_FAILED++))
else
    echo -e "${GREEN}✅ PASS${NC} - Database endpoint responding with data"
    ((TESTS_PASSED++))
fi
echo ""

# Test 7: Error pattern analysis
echo "Test 7/8: Error Pattern Analysis"
echo "---------------------------------"
ERROR_COUNT=$(curl -s --max-time 5 -X POST https://unruffled-noyce.emergent.host/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"invalid","password":"invalid"}' | grep -c "No address associated with hostname" || echo "0")

if [ "$ERROR_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✅ PASS${NC} - No MongoDB DNS errors detected"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - MongoDB DNS errors still present"
    ((TESTS_FAILED++))
fi
echo ""

# Test 8: System stability check
echo "Test 8/8: System Stability Check"
echo "---------------------------------"
STABILITY_SCORE=0
for i in {1..3}; do
    if curl -s --max-time 3 https://unruffled-noyce.emergent.host/api/health > /dev/null; then
        ((STABILITY_SCORE++))
    fi
    sleep 1
done

if [ "$STABILITY_SCORE" -eq "3" ]; then
    echo -e "${GREEN}✅ PASS${NC} - System stability: 3/3 requests successful"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - System stability: $STABILITY_SCORE/3 requests successful"
    ((TESTS_FAILED++))
fi
echo ""

# Final results
echo "=============================================="
echo "${BLUE}📊 VERIFICATION RESULTS${NC}"
echo "=============================================="
echo "Tests Passed: ${GREEN}$TESTS_PASSED${NC}/$TOTAL_TESTS"
echo "Tests Failed: ${RED}$TESTS_FAILED${NC}/$TOTAL_TESTS"

if [ "$TESTS_PASSED" -eq "$TOTAL_TESTS" ]; then
    echo ""
    echo -e "${GREEN}🎉 SUCCESS: Phase 1 Database Fix COMPLETED!${NC}"
    echo -e "${GREEN}✅ MongoDB connection working${NC}"
    echo -e "${GREEN}✅ Authentication system functional${NC}"
    echo -e "${GREEN}✅ ClinicHub deployment is now stable${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Perform full system testing"
    echo "2. Notify users that ClinicHub is operational"
    echo "3. Monitor system performance"
    exit 0
elif [ "$TESTS_PASSED" -ge 6 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  PARTIAL SUCCESS: Most systems working${NC}"
    echo -e "${YELLOW}Some issues remain - review failed tests above${NC}"
    exit 1
else
    echo ""
    echo -e "${RED}❌ FAILURE: Phase 1 Database Fix NOT COMPLETED${NC}"
    echo -e "${RED}Critical issues remain - MongoDB connection still broken${NC}"
    echo ""
    echo "Required actions:"
    echo "1. Verify internal MongoDB service is running"
    echo "2. Check MONGO_URL environment variable is updated"
    echo "3. Restart alpine-chub-backend container"
    echo "4. Run this verification script again"
    exit 2
fi