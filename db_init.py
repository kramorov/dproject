# db_init.py
import os
import django

def init_django():
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject1.settings") # Замените на ваше название
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        django.setup()