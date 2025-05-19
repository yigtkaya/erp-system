#!/bin/bash

# Script to import inventory data from backup file to the dev server
# Usage: ./import_inventory_data.sh [backup_file_path]

set -e

# Default backup file path
BACKUP_FILE=${1:-"backup.sql"}

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found."
    echo "Usage: ./import_inventory_data.sh [backup_file_path]"
    exit 1
fi

# Ensure we're in the project directory
PROJECT_DIR=$(dirname "$0")
cd "$PROJECT_DIR"

echo "Starting import process from $BACKUP_FILE"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the import command with a dry run first to check if it works
echo "Performing dry run to validate data..."
python manage.py import_inventory_from_backup "$BACKUP_FILE" --dry-run

# Ask for confirmation before proceeding
read -p "Do you want to proceed with the actual import? (y/n): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Import aborted."
    exit 0
fi

# Run the actual import
echo "Importing data..."
python manage.py import_inventory_from_backup "$BACKUP_FILE"

echo "Import process completed!" 