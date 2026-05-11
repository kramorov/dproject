import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from solenoid_valves.models import DirectionValve, ValveFunction
print(f"DirectionValve FILTER_DEFINITIONS: {len(DirectionValve.FILTER_DEFINITIONS)}")
print(f"ValveFunction has get_compatible_ids: {hasattr(ValveFunction, 'get_compatible_ids')}")

from core.models.smart_catalog_mixin import FilterType
print(f"FUNCTION_COMPATIBLE: {FilterType.FUNCTION_COMPATIBLE}")

print("\nAll OK")
