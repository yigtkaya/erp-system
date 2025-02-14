#!/bin/bash

# Exit on error
set -e

# Create log directory if it doesn't exist
mkdir -p /home/app/web/logs

# Wait for postgres
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py migrate
python manage.py collectstatic --no-input

exec "$@"