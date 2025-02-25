#!/bin/bash

# Exit on error
set -e

echo "Checking if static files are being served correctly..."
echo "Attempting to access admin CSS file..."

# Try to access the admin CSS file
curl -I http://68.183.213.111/static/admin/css/base.css

echo ""
echo "If you see a '200 OK' response above, static files are being served correctly."
echo "If you see a '404 Not Found' response, there's still an issue with static files." 