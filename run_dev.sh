#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install dev requirements
pip install -r requirements.dev.txt

# Start Redis for caching
docker-compose up -d redis

# Run development server
python manage.py migrate
python manage.py createsuperuser --noinput --username admin --email admin@example.com
python manage.py runserver 0.0.0.0:8000 