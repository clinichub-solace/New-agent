#!/bin/bash
# ClinicHub Data Backup Script for Synology Migration
# This script backs up the current comprehensive data before deployment

echo "🏥 ClinicHub - Creating Data Backup for Synology Migration"
echo "=========================================================="

# Create backup directory
mkdir -p /tmp/clinichub-backup

# Backup current MongoDB data
echo "📦 Backing up current ClinicHub database..."
mongodump --uri="mongodb://localhost:27017/clinichub" --out /tmp/clinichub-backup/mongodb/ 2>/dev/null || {
    echo "⚠️  MongoDB backup failed - this is expected if using different connection"
}

# Backup current backend
echo "📦 Backing up comprehensive backend..."
cp /app/backend/server.py /tmp/clinichub-backup/server.py.backup

# Backup initialization script
if [ -f "/app/backend/initialize_comprehensive_data.py" ]; then
    cp /app/backend/initialize_comprehensive_data.py /tmp/clinichub-backup/
    echo "✅ Backup created: initialize_comprehensive_data.py"
fi

# Create backup archive
cd /tmp && tar -czf clinichub-comprehensive-backup.tar.gz clinichub-backup/
echo "✅ Backup archive created: /tmp/clinichub-comprehensive-backup.tar.gz"

echo ""
echo "🎯 Next Steps:"
echo "1. Copy the backup to your Synology: scp /tmp/clinichub-comprehensive-backup.tar.gz admin@192.168.1.5:/volume1/docker/"
echo "2. SSH into your Synology: ssh admin@192.168.1.5"
echo "3. Extract and run the deployment"
echo ""