#!/bin/sh
set -e

echo "DATABASE_URL: $DATABASE_URL"
echo "Waiting for database to be ready..."

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting application..."
exec "$@"
