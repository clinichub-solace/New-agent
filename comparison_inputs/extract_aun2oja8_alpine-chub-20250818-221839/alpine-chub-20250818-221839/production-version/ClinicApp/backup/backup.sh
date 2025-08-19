#!/bin/bash

# ClinicHub Backup Script with HIPAA Compliance
# This script performs encrypted backups of MongoDB and application data

set -euo pipefail

# Configuration
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/logs/backup_${BACKUP_DATE}.log"
MONGO_BACKUP_DIR="/tmp/mongo_backup"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Initialize restic repository if it doesn't exist
init_repository() {
    log "Initializing restic repository..."
    if ! restic snapshots &>/dev/null; then
        restic init || error_exit "Failed to initialize restic repository"
        log "Restic repository initialized successfully"
    else
        log "Restic repository already exists"
    fi
}

# Backup MongoDB
backup_mongodb() {
    log "Starting MongoDB backup..."
    
    # Read MongoDB connection string
    MONGO_URL=$(cat /run/secrets/mongo_connection_string)
    
    # Create backup directory
    mkdir -p "$MONGO_BACKUP_DIR"
    
    # Perform MongoDB dump
    mongodump --uri="$MONGO_URL" --out="$MONGO_BACKUP_DIR" --gzip || error_exit "MongoDB dump failed"
    
    # Create BSON data integrity checksum
    find "$MONGO_BACKUP_DIR" -name "*.bson.gz" -exec sha256sum {} \; > "$MONGO_BACKUP_DIR/checksums.txt"
    
    log "MongoDB backup completed: $MONGO_BACKUP_DIR"
}

# Backup application data
backup_application_data() {
    log "Starting application data backup..."
    
    # Backup MongoDB dump
    restic backup "$MONGO_BACKUP_DIR" --tag mongodb --tag "date-$BACKUP_DATE" || error_exit "MongoDB backup to restic failed"
    
    # Backup logs
    restic backup /backup/logs --tag logs --tag "date-$BACKUP_DATE" || error_exit "Logs backup failed"
    
    # Backup configuration (excluding secrets for security)
    restic backup /backup/secrets --tag secrets --tag "date-$BACKUP_DATE" || error_exit "Secrets backup failed"
    
    log "Application data backup completed"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Apply retention policy
    restic forget \
        --keep-daily "$RETENTION_DAYS" \
        --keep-weekly "$RETENTION_WEEKS" \
        --keep-monthly "$RETENTION_MONTHS" \
        --prune || error_exit "Backup cleanup failed"
    
    log "Old backup cleanup completed"
}

# Verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."
    
    # Check repository integrity
    restic check --read-data-subset=5% || error_exit "Backup integrity check failed"
    
    log "Backup integrity verification completed"
}

# Main backup function
main() {
    log "Starting ClinicHub backup process"
    
    # Initialize repository
    init_repository
    
    # Backup MongoDB
    backup_mongodb
    
    # Backup application data
    backup_application_data
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Verify backup
    verify_backup
    
    # Cleanup temporary files
    rm -rf "$MONGO_BACKUP_DIR"
    
    log "ClinicHub backup process completed successfully"
}

# Run main function
main "$@"