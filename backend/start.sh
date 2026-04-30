#!/usr/bin/env bash
# exit on error
set -o errexit

cd backend

# Seed the database for testing/demo purposes
python manage.py seed_merchants

# Start Celery worker in the background with limited concurrency
celery -A config worker -l info --concurrency 1 &

# Start Gunicorn server in the foreground with 1 worker
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 2 --max-requests 50
