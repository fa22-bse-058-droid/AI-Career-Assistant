#!/bin/bash
set -e
python manage.py migrate --fake-initial 2>/dev/null || python manage.py migrate
exec "$@"