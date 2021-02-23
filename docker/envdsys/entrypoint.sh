#!/bin/bash

echo "hi test"
# python manage.py runserver 0.0.0.0:8001
# python manage.py runworker envnet-manage envdaq-manage &
export RUN_MAIN=true
daphne -b 0.0.0.0 -p 8001 envdsys.asgi:application