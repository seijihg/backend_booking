#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate --noinput
python manage.py seed_data

echo "Starting application..."
exec "$@"
