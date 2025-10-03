#!/bin/sh
set -e

echo "Waiting for database to be ready..."
python << END
import sys
import time
import psycopg2
from urllib.parse import urlparse
import os

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

parsed = urlparse(db_url)
max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            dbname=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port
        )
        conn.close()
        print("Database is ready!")
        break
    except psycopg2.OperationalError as e:
        retry_count += 1
        print(f"Database not ready yet ({retry_count}/{max_retries}). Waiting...")
        time.sleep(1)
else:
    print("ERROR: Could not connect to database after 30 seconds")
    sys.exit(1)
END

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting application..."
exec "$@"
