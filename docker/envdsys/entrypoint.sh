#!/bin/bash

echo "hi test"
# python manage.py runserver 0.0.0.0:8001
daphne -b 0.0.0.0 -p 8001 envdsys.asgi:application