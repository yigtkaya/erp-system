#!/bin/bash

# Exit on error
set -e

if [ -z "$1" ]; then
    echo "Please provide the backup file path"
    echo "Usage: ./restore.sh /path/to/full_backup_YYYYMMDD_HHMMSS.tar.gz"
    exit 1
fi

BACKUP_FILE=$1
RESTORE_DIR="/app/restore_temp"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🔄 Starting restore process..."

# Create temporary directory
mkdir -p $RESTORE_DIR
cd $RESTORE_DIR

# Extract the backup
echo "📦 Extracting backup..."
tar -xzf $BACKUP_FILE
BACKUP_FOLDER=$(ls)
cd $BACKUP_FOLDER

# Stop the services
echo "🛑 Stopping services..."
cd /app/erp-system
docker-compose -f docker-compose.prod.yml down

# Restore database
echo "💾 Restoring database..."
docker-compose -f docker-compose.prod.yml up -d db
sleep 10  # Wait for database to be ready
cat "${RESTORE_DIR}/${BACKUP_FOLDER}/database.sql" | docker-compose -f docker-compose.prod.yml exec -T db psql -U erp_admin erp_prod

# Restore media files
echo "🖼️ Restoring media files..."
tar -xzf "${RESTORE_DIR}/${BACKUP_FOLDER}/media.tar.gz" -C /app/erp-system/

# Restore environment files (optional)
echo "⚙️ Restoring environment files..."
cp "${RESTORE_DIR}/${BACKUP_FOLDER}/.env.prod" /app/erp-system/.env.prod.restored

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Clean up
echo "🧹 Cleaning up..."
rm -rf $RESTORE_DIR

echo "✅ Restore completed!"
echo "⚠️ Please verify the application is working correctly"
echo "📝 Note: A copy of the old .env.prod file has been saved as .env.prod.restored" 