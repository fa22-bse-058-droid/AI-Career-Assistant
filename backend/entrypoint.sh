#!/bin/bash
set -e
python manage.py migrate --fake-initial
exec "$@"
