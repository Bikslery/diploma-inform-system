#!/bin/sh
set -e

mkdir -p /app/data

if [ ! -f /app/data/db.sqlite3 ]; then
    python manage.py migrate --noinput
fi

python manage.py collectstatic --noinput

exec "$@"
