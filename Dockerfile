# Use the same base image
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (keep build essentials for psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=erp_core.settings_prod

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Use gunicorn instead of runserver
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "erp_core.wsgi:application"]