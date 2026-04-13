web: daphne -b 0.0.0.0 -p $PORT vibematch.asgi:application
release: python manage.py migrate && python manage.py seed_data
