import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
django.setup()
from solenoid_valves.models import ValveFunction
print('has get_compatible_ids:', hasattr(ValveFunction, 'get_compatible_ids'))
