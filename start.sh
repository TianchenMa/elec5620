#!/bin/bash

# Start Gunicorn processes
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('da', 'admin@example.com', 'admin123')" | python manage.py shell
echo Starting Gunicorn.
exec gunicorn elec5620.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3