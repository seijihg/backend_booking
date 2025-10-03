#!/bin/sh
set -e

echo "DATABASE_URL: $DATABASE_URL"

echo "Running database migrations..."
python manage.py migrate --noinput
python manage.py seed_data

echo "Starting application..."
exec "$@"
