#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py flush --no-input
python manage.py migrate

python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', '$ADMINPASS')"

python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('staff', 'staff@example.com', '$STAFFPASS', is_staff=True)"

exec "$@"
