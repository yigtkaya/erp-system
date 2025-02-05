#!/bin/bash

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    python3-pip \
    python3-dev \
    nginx \
    netcat

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Create app directory
sudo mkdir -p /app
sudo chown $USER:$USER /app

# Install Python dependencies
pip3 install docker-compose

# Basic firewall setup
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw --force enable

echo "Server setup completed! Please log out and log back in for docker group changes to take effect." 