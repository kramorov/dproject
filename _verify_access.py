"""Quick access system verification — uses real DB (no test DB setup)."""
import os, sys, django
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
django.setup()

passed = 0
total = 8

# 1. Registry size
from core.object_registry import OBJECT_REGISTRY, validate_permissions, get_registry_as_list
count = len(OBJECT_REGISTRY)
assert count >= 20, f'Expected 20+, got {count}'
print(f'[1/8] PASS  Registry: {count} objects')
passed += 1

# 2. Key objects
required = [
    'admin.customers', 'admin.permissions', 'admin.media',
    'admin.sku', 'admin.prices', 'admin.certs',
    'ai.pipelines', 'ai.skills', 'ai.wizard', 'ai.debug',
    'configurator.pa', 'configurator.ea',
    'catalog.pa', 'catalog.gearbox', 'catalog.ea',
]
for c in required:
    assert c in OBJECT_REGISTRY, f'Missing: {c}'
print(f'[2/8] PASS  All {len(required)} key objects present')
passed += 1

# 3. validate_permissions
w = validate_permissions({'nonexistent.obj': ['view']})
assert len(w) == 1, f'Expected 1 warning, got {len(w)}'
w2 = validate_permissions({'admin.customers': ['view']})
assert len(w2) == 0, f'Expected 0 warnings, got {len(w2)}'
print('[3/8] PASS  validate_permissions')
passed += 1

# 4. SystemGroup model
from project_customers.models import SystemGroup
g = SystemGroup.objects.create(
    code='_verify_group', name='Verify',
    object_permissions={'admin.customers': ['view', 'edit'], 'ai.debug': ['manage']}
)
assert g.has_action('admin.customers', 'view')
assert g.has_action('admin.customers', 'edit')
assert not g.has_action('admin.customers', 'delete')
assert g.has_action('ai.debug', 'delete')   # manage → all
print('[4/8] PASS  SystemGroup model')
passed += 1

# 5. ProjectCustomerUser
from project_customers.models import ProjectCustomer, ProjectCustomerUser
cust = ProjectCustomer.objects.create(name='_VerifyCorp')
user = ProjectCustomerUser.objects.create(
    customer=cust, login='_verifier', first_name='V', last_name='F'
)
user.system_groups.add(g)
assert user.has_system_perm('admin.customers', 'view')
assert user.has_system_perm('admin.customers', 'edit')
assert not user.has_system_perm('admin.customers', 'delete')
assert user.has_system_perm('ai.debug', 'delete')
perms = user.get_object_permissions()
assert 'admin.customers' in perms
assert 'ai.debug' in perms
assert 'manage' in perms['ai.debug']
print('[5/8] PASS  ProjectCustomerUser methods')
passed += 1

# 6. SiteSection split
from project_customers.models import SiteSection
scount = SiteSection.objects.count()
assert scount >= 17, f'Expected 17+, got {scount}'
for old_code in ['catalog', 'configurator']:
    s = SiteSection.objects.get(code=old_code)
    assert not s.is_active, f'{old_code} should be inactive'
new_codes = [
    'catalog_gearbox', 'catalog_pa', 'catalog_ea', 'catalog_lsb',
    'catalog_sv', 'catalog_fr', 'catalog_pf', 'catalog_cg',
    'configurator_pa', 'configurator_ea', 'configurator_cab',
]
for code in new_codes:
    s = SiteSection.objects.get(code=code)
    assert s.is_active, f'{code} should be active'
for s in SiteSection.objects.all():
    assert s.category, f'{s.code} has no category'
print(f'[6/8] PASS  SiteSection split ({scount} sections)')
passed += 1

# 7. related_name members
assert user in g.members.all(), 'FAIL: related_name'
print('[7/8] PASS  related_name members')
passed += 1

# 8. get_registry_as_list
items = get_registry_as_list()
assert isinstance(items, list) and len(items) > 10
assert 'codename' in items[0] and 'name' in items[0] and 'type' in items[0]
print('[8/8] PASS  get_registry_as_list')
passed += 1

# Cleanup
g.delete()
cust.delete()
print(f'\n===== ALL {passed}/{total} TESTS PASSED =====')
