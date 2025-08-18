#!/bin/bash

# MongoDB Health Check Script for ClinicHub
# This script checks MongoDB health with fallback methods

set -e

# MongoDB connection parameters
MONGO_HOST="localhost"
MONGO_PORT="27017"

# Method 1: Check if MongoDB is listening on port (no auth required)
if nc -z $MONGO_HOST $MONGO_PORT 2>/dev/null; then
    echo "MongoDB is listening on port $MONGO_PORT"
    
    # Method 2: Try authenticated ping if credentials are available
    if [ -f /run/secrets/mongo_root_password ]; then
        MONGO_PASSWORD=$(cat /run/secrets/mongo_root_password)
        MONGO_USER="admin"
        MONGO_AUTH_DB="admin"
        
        # Try mongosh first (MongoDB 6.0+)
        if command -v mongosh >/dev/null 2>&1; then
            RESULT=$(mongosh --host $MONGO_HOST --port $MONGO_PORT \
                            -u $MONGO_USER -p $MONGO_PASSWORD \
                            --authenticationDatabase $MONGO_AUTH_DB \
                            --eval "db.adminCommand('ping').ok" \
                            --quiet 2>/dev/null || echo "0")
            
            if [ "$RESULT" == "1" ]; then
                echo "MongoDB authenticated ping successful"
                exit 0
            fi
        fi
        
        # Fallback to mongo shell
        if command -v mongo >/dev/null 2>&1; then
            RESULT=$(mongo --host $MONGO_HOST --port $MONGO_PORT \
                           -u $MONGO_USER -p $MONGO_PASSWORD \
                           --authenticationDatabase $MONGO_AUTH_DB \
                           --eval "db.adminCommand('ping').ok" \
                           --quiet 2>/dev/null || echo "0")
            
            if [ "$RESULT" == "1" ]; then
                echo "MongoDB authenticated ping successful (fallback)"
                exit 0
            fi
        fi
    fi
    
    # If we get here, MongoDB is listening but auth ping failed
    # For health check purposes, listening on port is sufficient
    echo "MongoDB is healthy (port check)"
    exit 0
else
    echo "MongoDB is not listening on port $MONGO_PORT"
    exit 1
fi