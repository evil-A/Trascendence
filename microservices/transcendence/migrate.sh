#!/bin/sh

postgres_ready() {
    python << END
import sys
import os
from psycopg2 import connect
from psycopg2.errors import OperationalError

try:
    connect(
        dbname= os.getenv("DB_NAME"),
        user= os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host= os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
except OperationalError:
    sys.exit(-1)
END
}

echo "Waiting for postgres..."
#while ! nc -z $DB_HOST $DB_PORT; do
while ! python3 -c "import socket; socket.create_connection(('db', 5432))" 2>/dev/null; do
#until postgres_ready
#do
    sleep 1
done
echo "database connected"

export DJANGO_SETTINGS_MODULE=transcendence.settings

echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Crea superusuario solo si no existe
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser("admin", "admin@example.com", "password")
END

echo "Starting Daphne..."
DJANGO_SETTINGS_MODULE=transcendence.settings daphne -b 0.0.0.0 -p 8000 transcendence.asgi:application
#daphne -b 0.0.0.0 -p 8000 transcendence.asgi:application


#python manage.py createsuperuser --noinput
#python manage.py runserver 0.0.0.0:8000
