#!/bin/bash

# Exit on error
set -e

echo "Stopping production services..."
docker-compose -f docker-compose.prod.yml down

echo "Starting production services..."
docker-compose -f docker-compose.prod.yml up -d

echo "Waiting for services to start..."
sleep 10

echo "Checking container status..."
docker-compose -f docker-compose.prod.yml ps

echo "Production services restarted successfully!" 