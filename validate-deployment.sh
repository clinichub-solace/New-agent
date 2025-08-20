#!/bin/bash
# ClinicHub Deployment Validation Script

echo "🔍 ClinicHub Deployment Validation"
echo "=================================="

# Check if required environment variables are set
echo ""
echo "📋 Environment Variables Check:"

# Backend environment variables
if [ -z "$MONGO_URL" ]; then
    echo "❌ MONGO_URL not set - CRITICAL: Backend will fail to start"
else
    echo "✅ MONGO_URL is set"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ SECRET_KEY not set - Backend will use fallback"
else
    echo "✅ SECRET_KEY is set"
fi

if [ -z "$JWT_SECRET_KEY" ]; then
    echo "❌ JWT_SECRET_KEY not set - Backend will use fallback"  
else
    echo "✅ JWT_SECRET_KEY is set"
fi

# Frontend environment variables
if [ -z "$REACT_APP_BACKEND_URL" ]; then
    echo "⚠️ REACT_APP_BACKEND_URL not set - Will use fallback '/api'"
else
    echo "✅ REACT_APP_BACKEND_URL is set to: $REACT_APP_BACKEND_URL"
fi

# Check port configuration
echo ""
echo "🌐 Port Configuration:"
echo "Backend should bind to: 0.0.0.0:8001"
echo "Frontend should bind to: 0.0.0.0:3000"

# Check if services are running
echo ""
echo "🚀 Service Status:"

# Test backend health endpoint
if curl -f http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✅ Backend is running and healthy"
else
    echo "❌ Backend is not responding - Check logs for database connection issues"
fi

# Test frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"  
fi

# Database connectivity test
echo ""
echo "💾 Database Connectivity:"
if [ -n "$MONGO_URL" ]; then
    # Extract hostname from MongoDB URL for basic connectivity test
    MONGO_HOST=$(echo "$MONGO_URL" | sed 's/.*@\([^:]*\):.*/\1/')
    if [ -n "$MONGO_HOST" ] && [ "$MONGO_HOST" != "localhost" ] && [ "$MONGO_HOST" != "mongodb" ]; then
        if nslookup "$MONGO_HOST" > /dev/null 2>&1; then
            echo "✅ MongoDB hostname '$MONGO_HOST' resolves"
        else
            echo "❌ MongoDB hostname '$MONGO_HOST' does not resolve - DNS issue"
        fi
    fi
else
    echo "⚠️ Cannot test database connectivity - MONGO_URL not set"
fi

echo ""
echo "📝 Deployment Checklist:"
echo "1. ✅ Remove hardcoded database fallbacks from source code"
echo "2. ✅ Update frontend to use environment variables for API URLs"  
echo "3. ❓ Configure MONGO_URL secret to point to Emergent-managed MongoDB"
echo "4. ❓ Set SECRET_KEY and JWT_SECRET_KEY in Emergent secrets"
echo "5. ❓ Configure ingress to route /api/* to backend:8001"
echo "6. ❓ Configure ingress to route /* to frontend:3000"

echo ""
echo "🔧 Next Steps:"
echo "1. Update MONGO_URL in Emergent secrets to use accessible MongoDB instance"
echo "2. Redeploy application with updated configuration"
echo "3. Monitor backend logs for successful database connection"
echo "4. Test auth endpoints: /api/auth/signin"