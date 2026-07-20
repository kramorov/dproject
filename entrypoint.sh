#!/bin/sh
set -e

# Use external DB path if set, fallback to in-app
if [ -n "$DB_PATH" ]; then
    echo "Using DB at $DB_PATH"
fi

# Collect static
python manage.py collectstatic --noinput

# Migrate
python manage.py migrate --noinput

# Run
exec gunicorn djangoProject1.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
