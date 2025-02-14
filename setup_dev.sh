#!/bin/bash

# Exit on error
set -e

echo "Starting development environment setup..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "docker-compose is not installed. Please install it first."
    exit 1
fi

# Check if .env.dev exists
if [ ! -f .env.dev ]; then
    echo "Error: .env.dev file not found!"
    exit 1
fi

# Load environment variables
set -a
source .env.dev
set +a

# Create Docker network if it doesn't exist
echo "Setting up Docker network..."
docker network inspect erp_network >/dev/null 2>&1 || \
    docker network create erp_network

echo "Stopping any running containers..."
docker-compose -f docker-compose.dev.yml down -v

echo "Building images..."
docker-compose -f docker-compose.dev.yml build

echo "Starting database and Redis first..."
docker-compose -f docker-compose.dev.yml up -d db redis
echo "Waiting for database to be ready..."

# More robust database check with timeout
max_tries=30
count=0
while [ $count -lt $max_tries ]; do
    if docker-compose -f docker-compose.dev.yml exec db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
        echo "✅ Database is ready!"
        break
    fi
    count=$((count + 1))
    if [ $count -eq $max_tries ]; then
        echo "❌ Error: Database failed to start after $max_tries attempts"
        echo "Checking database logs:"
        docker-compose -f docker-compose.dev.yml logs db
        exit 1
    fi
    echo "Waiting for database... (Attempt $count/$max_tries)"
    sleep 2
done

echo "Starting web service..."
docker-compose -f docker-compose.dev.yml up -d web

echo "Running migrations..."
docker-compose -f docker-compose.dev.yml exec -T web python manage.py migrate || {
    echo "❌ Migration failed. Checking logs..."
    docker-compose -f docker-compose.dev.yml logs web
    exit 1
}

echo "Creating superuser..."
docker-compose -f docker-compose.dev.yml exec -T web python manage.py createsuperuser --noinput || true

# Check if services are running
echo "Checking if all services are running..."
services_status=$(docker-compose -f docker-compose.dev.yml ps)
if ! echo "$services_status" | grep -q "Up"; then
    echo "❌ Error: Some services failed to start. Current status:"
    echo "$services_status"
    echo "Checking logs:"
    docker-compose -f docker-compose.dev.yml logs
    exit 1
fi

# Test Django
echo "Testing Django development server..."
max_tries=15
count=0
while [ $count -lt $max_tries ]; do
    if curl -s http://68.183.213.111:8000/admin/ > /dev/null; then
        echo "✅ Django server is responding!"
        break
    fi
    count=$((count + 1))
    if [ $count -eq $max_tries ]; then
        echo "⚠️  Warning: Django server is not responding. Checking logs:"
        docker-compose -f docker-compose.dev.yml logs web
    fi
    echo "Waiting for Django server... (Attempt $count/$max_tries)"
    sleep 2
done

echo "✅ Setup complete! You can now access:"
echo "📝 API Documentation: http://68.183.213.111:8000/swagger/"
echo "👑 Admin Interface: http://68.183.213.111/admin/"
echo "🚀 API Interface: http://68.183.213.111:8000/api/"
echo ""
echo "Default superuser credentials:"
echo "👤 Username: admin"
echo "🔑 Password: admin123"
echo "📧 Email: admin@example.com"
echo ""
echo "Useful commands:"
echo "📋 View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "🛑 Stop services: docker-compose -f docker-compose.dev.yml down"
echo "🔄 Restart services: docker-compose -f docker-compose.dev.yml restart"
echo "🔍 Check service status: docker-compose -f docker-compose.dev.yml ps" 