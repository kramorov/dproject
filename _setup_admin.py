"""Create SystemGroup 'administrators' and assign to user 'kramorov'."""
import os, sys, django
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
django.setup()

from django.contrib.auth.models import User
from project_customers.models import (
    ProjectCustomer, ProjectCustomerUser, SystemGroup,
)
from core.object_registry import OBJECT_REGISTRY

# 1. Create "Система" organization if not exists
sys_org, created = ProjectCustomer.objects.get_or_create(
    name='Система',
    defaults={'short_name': 'SYS', 'is_active': True}
)
if created:
    print(f'Created organization: {sys_org.name} (id={sys_org.id})')
else:
    print(f'Organization exists: {sys_org.name} (id={sys_org.id})')

# 2. Create "administrators" group with FULL permissions on ALL objects
admin_group, created = SystemGroup.objects.get_or_create(
    code='administrators',
    defaults={
        'name': 'Администраторы',
        'is_default': False,
        'sorting_order': 0,
    }
)

# Grant manage on ALL registered objects
all_perms = {codename: ['manage'] for codename in OBJECT_REGISTRY}
admin_group.object_permissions = all_perms
admin_group.save()
print(f'Group "administrators": {len(all_perms)} objects with [manage]')

# 3. Create "authenticated_users" group (marker, no permissions)
auth_group, created = SystemGroup.objects.get_or_create(
    code='authenticated_users',
    defaults={
        'name': 'Авторизованные пользователи',
        'is_default': True,
        'sorting_order': 10,
    }
)
print(f'Group "authenticated_users": is_default={auth_group.is_default}')

# 4. Find Django user "kramorov"
django_user = User.objects.filter(username='kramorov').first()
if not django_user:
    print('ERROR: Django user "kramorov" not found!')
    sys.exit(1)

# 5. Find or create ProjectCustomerUser for kramorov under "Система"
profile, created = ProjectCustomerUser.objects.get_or_create(
    user=django_user,
    defaults={
        'customer': sys_org,
        'login': 'kramorov',
        'first_name': django_user.first_name or 'Admin',
        'last_name': django_user.last_name or 'System',
        'email': django_user.email or '',
        'is_active': True,
    }
)
if created:
    print(f'Created ProjectCustomerUser: {profile.login} (id={profile.id})')
else:
    print(f'ProjectCustomerUser exists: {profile.login} (id={profile.id})')
    # Ensure correct organization
    if profile.customer_id != sys_org.id:
        profile.customer = sys_org
        profile.save()
        print(f'  Moved to organization: {sys_org.name}')

# 6. Assign system_groups
profile.system_groups.add(admin_group)
print(f'Assigned group: {admin_group.code}')

# 7. Verify
profile.refresh_from_db()
groups = list(profile.system_groups.values_list('code', flat=True))
perms = profile.get_object_permissions()
print(f'\nVerification:')
print(f'  system_groups: {groups}')
print(f'  object_permissions count: {len(perms)}')
print(f'  has_system_perm("admin.customers","view"): {profile.has_system_perm("admin.customers","view")}')
print(f'\n===== SETUP COMPLETE =====')
