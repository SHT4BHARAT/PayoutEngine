#!/usr/bin/env bash
# exit on error
set -o errexit

cd backend

# Start Celery worker in the background
celery -A config worker -l info &

# Start Gunicorn server in the foreground
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
