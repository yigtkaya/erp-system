#!/bin/bash

# Exit on error
set -e

echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "Setting proper permissions..."
find staticfiles -type d -exec chmod 755 {} \;
find staticfiles -type f -exec chmod 644 {} \;

echo "Static files collection completed successfully!" 