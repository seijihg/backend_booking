web: python manage.py migrate && gunicorn --worker-tmp-dir /dev/shm booking_api.wsgi
worker: python manage.py rundramatiq