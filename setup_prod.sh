#!/bin/bash

# Exit on error
set -e

echo "Starting production environment setup..."

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

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "Error: .env.prod file not found!"
    exit 1
fi

# Load environment variables
set -a
source .env.prod
set +a

# Function to reset database
reset_database() {
    echo "Resetting database..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();"
    docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
    docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $POSTGRES_DB;"
}

# Create Docker network if it doesn't exist
echo "Setting up Docker network..."
docker network inspect erp_network >/dev/null 2>&1 || \
    docker network create erp_network

echo "Stopping any running containers..."
docker-compose -f docker-compose.prod.yml down -v

echo "Building images..."
docker-compose -f docker-compose.prod.yml build

echo "Starting database and Redis services first..."
docker-compose -f docker-compose.prod.yml up -d db redis
echo "Waiting for database to be ready..."

# More robust database check with timeout
max_tries=30
count=0
while [ $count -lt $max_tries ]; do
    if docker-compose -f docker-compose.prod.yml exec db pg_isready -U "$POSTGRES_USER" -d postgres; then
        echo "✅ Database is ready!"
        break
    fi
    count=$((count + 1))
    if [ $count -eq $max_tries ]; then
        echo "❌ Error: Database failed to start after $max_tries attempts"
        echo "Checking database logs:"
        docker-compose -f docker-compose.prod.yml logs db
        exit 1
    fi
    echo "Waiting for database... (Attempt $count/$max_tries)"
    sleep 2
done

# Reset database to ensure clean state
reset_database

echo "Running migrations..."
if ! docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate; then
    echo "❌ First migration attempt failed. Trying to fix..."
    reset_database
    if ! docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate; then
        echo "❌ Migration failed again. Checking logs..."
        docker-compose -f docker-compose.prod.yml logs web
        exit 1
    fi
fi

echo "Starting web service..."
docker-compose -f docker-compose.prod.yml up -d web

echo "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput || {
    echo "❌ collectstatic failed. Checking logs..."
    docker-compose -f docker-compose.prod.yml logs web
    exit 1
}

# Optionally, create a superuser if needed (not recommended for automated production setups)
# echo "Creating superuser..."
# docker-compose -f docker-compose.prod.yml exec -T web python manage.py createsuperuser --noinput || true

# Check if services are running
echo "Checking if all services are running..."
services_status=$(docker-compose -f docker-compose.prod.yml ps)
if ! echo "$services_status" | grep -q "Up"; then
    echo "❌ Error: Some services failed to start. Current status:"
    echo "$services_status"
    echo "Checking logs:"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

# Test Django production server if it's accessible
echo "Testing Django production server..."
max_tries=15
count=0
while [ $count -lt $max_tries ]; do
    if curl -s http://68.183.213.111/ > /dev/null; then
        echo "✅ Django production server is responding!"
        break
    fi
    count=$((count + 1))
    if [ $count -eq $max_tries ]; then
        echo "⚠️  Warning: Django production server is not responding. Checking logs:"
        docker-compose -f docker-compose.prod.yml logs web
    fi
    echo "Waiting for Django production server... (Attempt $count/$max_tries)"
    sleep 2
done

echo "✅ Production setup complete! Your application is now running."
echo "Access your application at: http://68.183.213.111/"
echo ""
echo "Useful commands:"
echo "📋 View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "🛑 Stop services: docker-compose -f docker-compose.prod.yml down"
echo "🔄 Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "🔍 Check service status: docker-compose -f docker-compose.prod.yml ps" 