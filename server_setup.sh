#!/bin/bash

# Exit on error
set -e

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Starting server setup..."

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 successful"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y
check_status "System update"

# Install required packages
echo "Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-full \
    pipx \
    nginx \
    netcat-openbsd \
    ufw \
    fail2ban \
    git
check_status "Package installation"

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    check_status "Docker installation"
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    check_status "Docker Compose installation"
else
    echo "Docker Compose already installed"
fi

# Add user to docker group
usermod -aG docker $SUDO_USER
check_status "User added to docker group"

# Create necessary directories
echo "Creating application directories..."
mkdir -p /app
mkdir -p /var/log/django
mkdir -p /app/nginx/certbot/conf
mkdir -p /app/nginx/certbot/www

# Set proper permissions
chown -R $SUDO_USER:$SUDO_USER /app
chown -R $SUDO_USER:$SUDO_USER /var/log/django
chmod -R 755 /var/log/django
check_status "Directory setup"

# Configure UFW
echo "Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable
check_status "Firewall configuration"

# Configure fail2ban
echo "Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban
check_status "Fail2ban configuration"

# Install Python dependencies
echo "Installing Python dependencies..."
# Create a virtual environment for global tools
VENV_PATH="/opt/venv"
python3 -m venv $VENV_PATH
source $VENV_PATH/bin/activate
$VENV_PATH/bin/pip install --upgrade pip
$VENV_PATH/bin/pip install docker-compose

# Create symlink for docker-compose if not installed via package manager
if [ ! -f "/usr/local/bin/docker-compose" ]; then
    ln -s $VENV_PATH/bin/docker-compose /usr/local/bin/docker-compose
fi

# Install pipx for isolated Python applications
pipx install docker-compose

check_status "Python dependencies installation"

# Basic security configurations
echo "Applying basic security configurations..."
# Disable root login via SSH
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
# Allow only SSH key authentication
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
check_status "Security configurations"

echo "✅ Server setup completed!"
echo ""
echo "🔧 Next steps:"
echo "1. Log out and log back in for docker group changes to take effect"
echo "2. Copy your project files to /app"
echo "3. Set up SSL certificates using certbot"
echo "4. Configure your environment variables"
echo ""
echo "🚀 To deploy your application:"
echo "1. cd /app"
echo "2. docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🔒 Security notes:"
echo "- SSH root login has been disabled"
echo "- Password authentication has been disabled (use SSH keys)"
echo "- UFW is configured to allow only SSH, HTTP, and HTTPS"
echo "- Fail2ban is active for additional security" 