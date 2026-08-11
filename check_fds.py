"""Check FILTER_DEFINITIONS on each model class."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django; django.setup()

from configurator.services.registry import get_product_model_class

codes = ['directional-valve', 'fr', 'manual-override', 'cable-gland',
         'lsb', 'fittings', 'pneumatic-actuator']

for c in codes:
    mc = get_product_model_class(c)
    fds = getattr(mc, 'FILTER_DEFINITIONS', None)
    has_smart_catalog = hasattr(mc, 'get_filter_options')
    print(f'{c:25s} FDs={len(fds) if fds else 0}  SmartCatalog={has_smart_catalog}')
