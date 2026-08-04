"""Add anonymous_users group."""
import os, sys, django
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
django.setup()

from project_customers.models import SystemGroup

g, created = SystemGroup.objects.get_or_create(
    code='anonymous_users',
    defaults={
        'name': 'Неавторизованные пользователи',
        'is_default': False,
        'sorting_order': 20,
        'object_permissions': {},
    }
)
print(f'anonymous_users: {"CREATED" if created else "EXISTS"} (id={g.id})')
