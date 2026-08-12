import os, sys
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')

import django
from django.conf import settings
_test_db = os.path.join(_PROJECT_ROOT, 'configurator_test_db.sqlite3')
if os.path.exists(_test_db):
    settings.DATABASES['default']['NAME'] = _test_db
    print(f'Using test DB: configurator_test_db.sqlite3')

from django.test.runner import DiscoverRunner
DiscoverRunner.setup_databases = lambda *a,**kw: []
DiscoverRunner.teardown_databases = lambda *a,**kw: None

django.setup()

# === QA Check 1: Import everything ===
print('\n=== QA CHECK 1: IMPORTS ===')
try:
    from configurator.models import (
        EquipmentTypeParameter, ParameterSource, ParameterRule,
        ParameterBinding, PropagationRule, DerivationRule,
        AssemblyRequirements, ComponentRequirement, FittingPattern,
    )
    from configurator.services.expander import expand_composition_group
    from configurator.services.resolver import resolve_effective_requirements, resolve_all_components
    from configurator.services.filter_engine import filter_by_requirements, select_product
    from configurator.services.cascade import cascade_after_select
    from configurator.services.registry import get_product_model_class, PRODUCT_MODEL_REGISTRY
    from configurator.api.views import (
        AssemblyListView, AssemblyDetailView, FilterSchemaView,
        ComponentDetailView, ComponentFilterView, ComponentSelectView,
    )
    from configurator.api.admin_views import (
        EquipmentTypeParameterViewSet, ParameterSourceViewSet,
        PropagationRuleViewSet, ParameterRuleViewSet, ParameterBindingViewSet, DerivationRuleViewSet,
    )
    print('  ALL IMPORTS: OK')
except Exception as e:
    print(f'  IMPORT FAILED: {e}')
    sys.exit(1)

# === QA Check 2: Data integrity ===
print('\n=== QA CHECK 2: DATA ===')
t = EquipmentTypeParameter.objects.filter(is_active=True).count()
print(f'  ETP total: {t}')
for field, label in [('source','source'), ('field_path','field_path'), ('compare_direction','compare_direction')]:
    filled = EquipmentTypeParameter.objects.filter(is_active=True, **{f'{field}__isnull': False}).count()
    empty = EquipmentTypeParameter.objects.filter(is_active=True, **{f'{field}__isnull': True}).count()
    if field == 'field_path':
        empty = EquipmentTypeParameter.objects.filter(is_active=True, field_path='').count()
        filled = t - empty
    print(f'  {label}: filled={filled} empty={empty}')

print(f'  ParameterSource: {ParameterSource.objects.count()}')
print(f'  ParameterRule active: {ParameterRule.objects.filter(is_active=True).count()}')
print(f'  ParameterBinding active: {ParameterBinding.objects.filter(is_active=True).count()}')
print(f'  PropagationRule active: {PropagationRule.objects.filter(is_active=True).count()}')
print(f'  Registry entries: {len(PRODUCT_MODEL_REGISTRY)}')

# === QA Check 3: API endpoints ===
print('\n=== QA CHECK 3: API ENDPOINTS ===')
from django.test.client import Client
import json
c = Client()

# Test anonymous access to configurator endpoints
endpoints = [
    ('POST', '/api/configurator/assemblies/', {'composition_group_id': 5, 'name': 'qa-test'}),
]
for method, url, data in endpoints:
    if method == 'POST':
        r = c.post(url, json.dumps(data), content_type='application/json')
    else:
        r = c.get(url)
    ok = 'OK' if r.status_code in (200, 201, 302) else f'FAIL({r.status_code})'
    print(f'  {method} {url}: {ok}')

# Admin endpoints
admin_urls = [
    '/api/configurator/admin/equipment-type-parameters/',
    '/api/configurator/admin/parameter-sources/',
]
for url in admin_urls:
    r = c.get(url)
    ok = 'OK' if r.status_code in (200, 201) else f'FAIL({r.status_code})'
    print(f'  GET {url}: {ok}')

# Filter schema
r = c.get('/api/configurator/equipment-types/8/filter-schema/')  # lsb id=8
print(f'  GET /equipment-types/8/filter-schema/: {"OK" if r.status_code == 200 else f"FAIL({r.status_code})"}')

# === QA Check 4: URL resolution ===
print('\n=== QA CHECK 4: URL RESOLUTION ===')
from django.urls import resolve, get_resolver
test_urls = [
    '/api/configurator/assemblies/',
    '/api/configurator/components/1/filter/',
    '/api/configurator/admin/equipment-type-parameters/',
    '/api/configurator/admin/parameter-sources/',
]
for url in test_urls:
    try:
        match = resolve(url)
        print(f'  {url}: {match.view_name}')
    except Exception as e:
        print(f'  {url}: NOT FOUND ({e})')
