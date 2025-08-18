#!/bin/bash

# Test MongoDB 4.4 Health Check
echo "Testing MongoDB 4.4 Health Check..."

echo "1. Testing mongo command directly in container..."
docker exec clinichub-mongodb mongo --eval "db.adminCommand('ping')"

echo ""
echo "2. Checking container health status..."
HEALTH_STATUS=$(docker inspect clinichub-mongodb --format='{{.State.Health.Status}}')
echo "Current Health Status: $HEALTH_STATUS"

echo ""
echo "3. Checking last few health check results..."
docker inspect clinichub-mongodb --format='{{range .State.Health.Log}}{{.Output}}{{end}}' | tail -n 5

echo ""
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✅ MongoDB 4.4 health check is working!"
else
    echo "❌ MongoDB 4.4 health check needs attention. Status: $HEALTH_STATUS"
fi