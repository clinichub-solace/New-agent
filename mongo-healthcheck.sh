#!/bin/bash

# MongoDB Health Check Script for ClinicHub
# This script checks MongoDB health with authentication

set -e

# Read MongoDB credentials from Docker secrets
if [ -f /run/secrets/mongo_root_password ]; then
    MONGO_PASSWORD=$(cat /run/secrets/mongo_root_password)
else
    echo "MongoDB password secret not found"
    exit 1
fi

# MongoDB connection parameters
MONGO_USER="admin"
MONGO_HOST="localhost"
MONGO_PORT="27017"
MONGO_AUTH_DB="admin"

# Check MongoDB health using mongosh (MongoDB 6.0+)
if command -v mongosh >/dev/null 2>&1; then
    RESULT=$(mongosh --host $MONGO_HOST --port $MONGO_PORT \
                    -u $MONGO_USER -p $MONGO_PASSWORD \
                    --authenticationDatabase $MONGO_AUTH_DB \
                    --eval "db.adminCommand('ping').ok" \
                    --quiet 2>/dev/null || echo "0")
# Fallback to mongo shell for older versions
elif command -v mongo >/dev/null 2>&1; then
    RESULT=$(mongo --host $MONGO_HOST --port $MONGO_PORT \
                   -u $MONGO_USER -p $MONGO_PASSWORD \
                   --authenticationDatabase $MONGO_AUTH_DB \
                   --eval "db.adminCommand('ping').ok" \
                   --quiet 2>/dev/null || echo "0")
else
    echo "Neither mongosh nor mongo command found"
    exit 1
fi

# Check if ping was successful
if [ "$RESULT" == "1" ]; then
    echo "MongoDB is healthy"
    exit 0
else
    echo "MongoDB health check failed"
    exit 1
fi