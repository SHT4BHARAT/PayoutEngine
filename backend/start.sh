#!/usr/bin/env bash
# exit on error
set -o errexit

cd backend

# Seed the database for testing/demo purposes
python manage.py seed_merchants

# Start Celery worker in the background
celery -A config worker -l info &

# Start Gunicorn server in the foreground
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
