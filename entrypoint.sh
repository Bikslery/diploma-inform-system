#!/bin/sh
set -e

mkdir -p /app/data

if [ ! -f /app/data/db.sqlite3 ]; then
    python manage.py migrate --noinput
    python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin','admin@company.com','admin123')"
fi

python manage.py collectstatic --noinput

exec "$@"
