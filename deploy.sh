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
DEBUG=False
SECRET_KEY="!6l@*-lf#5jed550yx!bt30w)%@&#o+-j*svjuh8@le9%hh+$="
DJANGO_SETTINGS_MODULE=erp_core.settings.production
ALLOWED_HOSTS=68.183.213.111,kapsam-erp.vercel.app
DJANGO_ADMIN_URL=admin

# Security
CSRF_TRUSTED_ORIGINS=http://68.183.213.111,https://kapsam-erp.vercel.app
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_REFERRER_POLICY=same-origin
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# PostgreSQL Database Configuration
POSTGRES_DB=erp_prod
POSTGRES_USER=erp_admin
POSTGRES_PASSWORD=erp_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
DB_CONNECT_TIMEOUT=5

# Redis
REDIS_URL=redis://redis:6379/1
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

# Email
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password

# File Storage
MEDIA_ROOT=/home/app/web/media
STATIC_ROOT=/home/app/web/staticfiles

# CLOUDFLARE R2 settings
CLOUDFLARE_R2_ACCESS_KEY=a0ed21e3517b7d8b3658bee5cf1d5d1d
CLOUDFLARE_R2_SECRET_KEY=ac2ea29cd00e525e7d6ede8e4c43fddd299a501c68c8ae177bccaf2b90664b8f
CLOUDFLARE_R2_BUCKET_NAME=kapsammakina
CLOUDFLARE_R2_BUCKET_ENDPOINT=https://c8149980d3283c2362a57216a4b63281.r2.cloudflarestorage.com

# Email settings
MAILGUN_API_KEY=your-production-mailgun-api-key
MAILGUN_SENDER_DOMAIN=your-domain.com

# CORS settings
CORS_ALLOWED_ORIGINS=https://kapsam-erp.vercel.app
CORS_ALLOW_CREDENTIALS=True
CORS_EXPOSE_HEADERS=Content-Type,Authorization


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

# Add before line 175 (docker-compose up command)
echo "🏗️ Initializing Certbot..."
docker-compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path /var/www/certbot/ -d your-domain.com

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