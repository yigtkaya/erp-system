#!/bin/bash

# Script to import inventory data from backup file to the Docker dev server
# Usage: ./docker_import_inventory.sh [backup_file_path]

set -e

# Default backup file path
BACKUP_FILE=${1:-"backup.sql"}

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found."
    echo "Usage: ./docker_import_inventory.sh [backup_file_path]"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not installed."
    exit 1
fi

# Check if docker-compose.dev.yml exists
if [ ! -f "docker-compose.dev.yml" ]; then
    echo "Error: docker-compose.dev.yml not found in the current directory."
    exit 1
fi

echo "Starting import process from $BACKUP_FILE in Docker environment"

# Run the import command with a dry run first to check if it works
echo "Performing dry run to validate data..."
docker compose -f docker-compose.dev.yml exec web python manage.py import_inventory_from_backup /app/$BACKUP_FILE --dry-run

# Ask for confirmation before proceeding
read -p "Do you want to proceed with the actual import? (y/n): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Import aborted."
    exit 0
fi

# Run the actual import
echo "Importing data..."
docker compose -f docker-compose.dev.yml exec web python manage.py import_inventory_from_backup /app/$BACKUP_FILE

echo "Import process completed!" 