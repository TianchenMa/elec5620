#!/bin/bash

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn elec5620.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3