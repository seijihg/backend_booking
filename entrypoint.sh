#!/bin/sh
set -e

# Run health checks for external services
echo "Running health checks..."
python manage.py healthcheck --fail-fast

echo "Running database migrations..."
python manage.py migrate --noinput
python manage.py seed_data

echo "Starting application..."
exec "$@"
