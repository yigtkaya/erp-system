#!/bin/bash

# Stop any running containers and remove them
docker-compose -f docker-compose.dev.yml down -v

# Build the images
docker-compose -f docker-compose.dev.yml build

# Start the services
docker-compose -f docker-compose.dev.yml up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run migrations
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser --noinput

echo "Setup complete! You can now access:"
echo "- API Documentation: http://localhost:8000/swagger/"
echo "- Admin Interface: http://localhost:8000/admin/"
echo "- API Interface: http://localhost:8000/api/"
echo ""
echo "Default superuser credentials:"
echo "Username: admin"
echo "Password: admin123"
echo "Email: admin@example.com" 