#!/bin/sh

# Install netcat if not present
apt-get update && apt-get install -y netcat-openbsd

# Wait for postgres
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

exec "$@"