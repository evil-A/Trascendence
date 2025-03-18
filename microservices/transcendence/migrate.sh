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

until postgres_ready
do
    sleep 0.1
done

echo "database connected"

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --noinput

export DJANGO_SETTINGS_MODULE=transcendence.settings
python manage.py collectstatic --noinput
daphne -e ssl:8000:privateKey=/key.pem:certKey=/cert.pem transcendence.asgi:application
#python manage.py runserver 0.0.0.0:8000