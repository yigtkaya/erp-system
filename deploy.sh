#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting deployment process..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    python3-pip \
    python3-dev \
    nginx \
    git \
    ufw

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Setup firewall
echo "🛡️ Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw --force enable

# Create app directory
echo "📁 Creating application directory..."
sudo mkdir -p /app
sudo chown $USER:$USER /app

# Handle existing repository
echo "📥 Setting up repository..."
cd /app
if [ -d "erp-system" ]; then
    echo "Repository directory exists. Removing it..."
    sudo rm -rf erp-system
fi

# Clone the repository
echo "Cloning fresh repository..."
git clone https://github.com/yigtkaya/erp-system.git
cd erp-system

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p media staticfiles static
chmod -R 755 media staticfiles static

# Create environment files
echo "⚙️ Creating environment files..."

# Create .env.prod
cat > .env.prod << EOL
# Django
DEBUG=0
SECRET_KEY=*u3e%1k&h^if%*fzk7#(=-#f#cwdbeqmx39hakmj-wo414bfyi
DJANGO_SETTINGS_MODULE=erp_core.settings
ALLOWED_HOSTS=localhost,127.0.0.1,68.183.213.111
DATABASE=postgres

# Security
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,http://68.183.213.111
SECURE_SSL_REDIRECT=0
SESSION_COOKIE_SECURE=0
CSRF_COOKIE_SECURE=0
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=0
SECURE_HSTS_PRELOAD=0
SECURE_REFERRER_POLICY=same-origin

# Database
DB_NAME=erp_prod
DB_USER=erp_admin
DB_PASSWORD=erp_password
DB_HOST=db
DB_PORT=5432
DB_CONNECT_TIMEOUT=5

# PostgreSQL
POSTGRES_DB=erp_prod
POSTGRES_USER=erp_admin
POSTGRES_PASSWORD=erp_password

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_CONNECT_TIMEOUT=5
REDIS_SOCKET_TIMEOUT=5

# Session
SESSION_COOKIE_AGE=86400

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=1
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True
JWT_ALGORITHM=HS256

# Rate Limiting
AXES_FAILURE_LIMIT=5
AXES_COOLOFF_TIME=1

# URLs
LOGIN_URL=login
LOGIN_REDIRECT_URL=home
LOGOUT_REDIRECT_URL=login

# File Storage
MEDIA_ROOT=/home/app/web/media
STATIC_ROOT=/home/app/web/staticfiles
EOL

# Create .env.prod.db
cat > .env.prod.db << EOL
POSTGRES_DB=erp_prod
POSTGRES_USER=erp_admin
POSTGRES_PASSWORD=erp_password
EOL

# Make scripts executable
chmod +x entrypoint.prod.sh

# Stop system Nginx and any running containers
echo "🛑 Stopping services..."
sudo systemctl stop nginx
sudo systemctl disable nginx
docker-compose -f docker-compose.prod.yml down -v || true

# Check and kill any process using port 80
echo "Checking for processes using port 80..."
sudo lsof -i :80 | grep LISTEN | awk '{print $2}' | xargs -r sudo kill -9

# Build and start containers
echo "🏗️ Building and starting containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Apply migrations
echo "🔄 Applying database migrations..."
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

# Collect static files
echo "📚 Collecting static files..."
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
echo "👤 Creating superuser..."
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

echo "✅ Deployment completed!"
echo "🌍 Your application should now be accessible at http://68.183.213.111"
echo "⚠️ Make sure to:"
echo "  1. Update your .env.prod file with proper credentials"
echo "  2. Configure your domain and SSL certificate if needed"
echo "  3. Regularly backup your database"