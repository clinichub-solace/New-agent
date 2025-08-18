#!/bin/bash

# Test script to verify MongoDB health check
echo "Testing MongoDB Health Check Fix..."

echo "1. Checking if MongoDB container is running..."
if docker ps | grep -q clinichub-mongodb; then
    echo "✅ MongoDB container is running"
else
    echo "❌ MongoDB container is not running"
    exit 1
fi

echo ""
echo "2. Testing health check command directly in container..."
docker exec clinichub-mongodb mongosh --host localhost --port 27017 --authenticationDatabase admin -u admin -p "$(docker exec clinichub-mongodb cat /run/secrets/mongo_root_password)" --eval 'db.adminCommand("ping")' --quiet

echo ""
echo "3. Checking container health status..."
HEALTH_STATUS=$(docker inspect clinichub-mongodb --format='{{.State.Health.Status}}')
echo "Health Status: $HEALTH_STATUS"

echo ""
echo "4. Checking health check logs..."
docker inspect clinichub-mongodb --format='{{range .State.Health.Log}}{{.Output}}{{end}}'

echo ""
echo "MongoDB Health Check Test Complete!"