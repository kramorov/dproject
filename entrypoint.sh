#!/bin/sh
set -e

# Use external DB path if set, fallback to in-app
if [ -n "$DB_PATH" ]; then
    DB_DIR=$(dirname "$DB_PATH")
    if [ ! -f "$DB_PATH" ]; then
        echo "DB not found at $DB_PATH, copying from image..."
        mkdir -p "$DB_DIR"
        cp /app/db.sqlite3 "$DB_PATH"
        echo "DB copied to $DB_PATH"
    fi
    echo "Using DB at $DB_PATH"
fi

# Apply pending migrations (schema must match the shipped code)
python manage.py migrate --noinput

# Run
exec gunicorn djangoProject1.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    --worker-tmp-dir /tmp \
    --access-logfile - \
    --error-logfile -
