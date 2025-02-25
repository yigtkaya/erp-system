#!/bin/bash

# Exit on error
set -e

echo "Stopping Nginx container..."
docker-compose -f docker-compose.prod.yml stop nginx

echo "Removing Nginx container..."
docker-compose -f docker-compose.prod.yml rm -f nginx

echo "Rebuilding Nginx container..."
docker-compose -f docker-compose.prod.yml build nginx

echo "Starting Nginx container..."
docker-compose -f docker-compose.prod.yml up -d nginx

echo "Nginx container rebuilt and restarted successfully!" 