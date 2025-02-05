#!/bin/bash

# Exit on error
set -e

# Configuration
BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"
RETAIN_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup directory for this backup
mkdir -p $BACKUP_PATH

echo "📦 Starting backup process..."

# Backup PostgreSQL database
echo "💾 Backing up database..."
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U erp_admin erp_prod > "${BACKUP_PATH}/database.sql"

# Backup media files
echo "🖼️ Backing up media files..."
tar -czf "${BACKUP_PATH}/media.tar.gz" -C /app/erp-system media/

# Backup environment files
echo "⚙️ Backing up environment files..."
cp /app/erp-system/.env.prod "${BACKUP_PATH}/"

# Create a single archive of all backups
tar -czf "${BACKUP_DIR}/full_backup_${TIMESTAMP}.tar.gz" -C $BACKUP_DIR "backup_${TIMESTAMP}"

# Clean up temporary files
rm -rf "${BACKUP_PATH}"

# Remove backups older than RETAIN_DAYS days
find $BACKUP_DIR -name "full_backup_*.tar.gz" -mtime +$RETAIN_DAYS -delete

# Optional: Copy to remote storage (uncomment and configure as needed)
# rclone copy "${BACKUP_DIR}/full_backup_${TIMESTAMP}.tar.gz" remote:erp-backups/

echo "✅ Backup completed! Backup file: ${BACKUP_DIR}/full_backup_${TIMESTAMP}.tar.gz"

# Send notification (uncomment and configure as needed)
# curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
#      -d "chat_id=${TELEGRAM_CHAT_ID}" \
#      -d "text=ERP System Backup Completed: ${TIMESTAMP}" 