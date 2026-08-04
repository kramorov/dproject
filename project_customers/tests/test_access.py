"""
Tests for access control: Object Registry, SystemGroup, SiteSection split,
SystemObjectPermission, OrgSectionPermission, /auth/me/ response.

Run: python manage.py test project_customers.tests.test_access
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser

from core.object_registry import (
    OBJECT_REGISTRY, register_object, get_registry_as_list, validate_permissions
)
from core.permissions import SystemObjectPermission, OrgSectionPermission
from project_customers.models import (
    ProjectCustomer, ProjectCustomerUser, SystemGroup,
    SiteSection, Role,
)


# ============================================================
# 1. Object Registry
# ============================================================

class ObjectRegistryTests(TestCase):
    """Auto-import from core/apps.py -> all app object_registry files."""

    def test_registry_not_empty(self):
        """At least 20 objects loaded from 5 apps."""
        self.assertGreaterEqual(len(OBJECT_REGISTRY), 20,
            f"Expected 20+ objects, got {len(OBJECT_REGISTRY)}")

    def test_key_objects_present(self):
        """All core admin/ai/catalog/configurator objects registered."""
        required = [
            'admin.customers', 'admin.permissions', 'admin.media',
            'admin.sku', 'admin.prices', 'admin.certs',
            'ai.pipelines', 'ai.skills', 'ai.wizard', 'ai.debug',
            'configurator.pa', 'configurator.ea',
            'catalog.pa', 'catalog.gearbox', 'catalog.ea',
        ]
        for codename in required:
            self.assertIn(codename, OBJECT_REGISTRY,
                f"Missing object: {codename}")

    def test_register_object(self):
        """register_object() adds to registry."""
        register_object(codename='test.dummy', name='Test Dummy', type='page')
        self.assertIn('test.dummy', OBJECT_REGISTRY)
        self.assertEqual(OBJECT_REGISTRY['test.dummy'].name, 'Test Dummy')

    def test_get_registry_as_list(self):
        """get_registry_as_list() returns list of dicts."""
        items = get_registry_as_list()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        self.assertIn('codename', items[0])
        self.assertIn('name', items[0])
        self.assertIn('type', items[0])

    def test_validate_permissions_unknown(self):
        """validate_permissions warns about unknown codenames."""
        warnings = validate_permissions({'nonexistent.object': ['view']})
        self.assertEqual(len(warnings), 1)
        self.assertIn('nonexistent.object', warnings[0])

    def test_validate_permissions_known(self):
        """validate_permissions returns empty for known codenames."""
        warnings = validate_permissions({'admin.customers': ['view']})
        self.assertEqual(len(warnings), 0)


# ============================================================
# 2. SystemGroup model
# ============================================================

class SystemGroupModelTests(TestCase):

    def test_create_group(self):
        group = SystemGroup.objects.create(
            code='testers',
            name='Testers',
            object_permissions={'admin.customers': ['view'], 'ai.debug': ['manage']},
        )
        self.assertEqual(group.code, 'testers')
        self.assertEqual(group.get_actions('admin.customers'), ['view'])
        self.assertTrue(group.has_action('admin.customers', 'view'))
        self.assertFalse(group.has_action('admin.customers', 'edit'))
        self.assertTrue(group.has_action('ai.debug', 'edit'))   # manage → all
        self.assertTrue(group.has_action('ai.debug', 'delete'))  # manage → all

    def test_group_is_default(self):
        group = SystemGroup.objects.create(code='defaults', name='Defaults', is_default=True)
        self.assertTrue(group.is_default)

    def test_group_str(self):
        group = SystemGroup.objects.create(code='admins', name='Admins')
        self.assertIn('Admins', str(group))
        self.assertIn('admins', str(group))


# ============================================================
# 3. SiteSection split
# ============================================================

class SiteSectionSplitTests(TestCase):

    def test_total_sections(self):
        """17 sections total: 6 original + 11 new split."""
        count = SiteSection.objects.count()
        self.assertGreaterEqual(count, 17, f"Expected 17+ sections, got {count}")

    def test_old_sections_deactivated(self):
        """catalog and configurator are inactive."""
        old = SiteSection.objects.filter(code__in=['catalog', 'configurator'])
        for s in old:
            self.assertFalse(s.is_active, f"{s.code} should be inactive")

    def test_new_sections_active(self):
        """All split sections are active."""
        new_codes = [
            'catalog_gearbox', 'catalog_pa', 'catalog_ea', 'catalog_lsb',
            'catalog_sv', 'catalog_fr', 'catalog_pf', 'catalog_cg',
            'configurator_pa', 'configurator_ea', 'configurator_cab',
        ]
        for code in new_codes:
            s = SiteSection.objects.get(code=code)
            self.assertTrue(s.is_active, f"{code} should be active")

    def test_categories_assigned(self):
        """Every section has a non-empty category."""
        for s in SiteSection.objects.all():
            self.assertNotEqual(s.category, '', f"{s.code} has no category")

    def test_category_values(self):
        """Categories are from allowed set."""
        expected_cats = {'catalog', 'configurator', 'admin', 'ai', 'requests'}
        cats = set(SiteSection.objects.values_list('category', flat=True))
        self.assertTrue(cats.issubset(expected_cats),
            f"Unexpected categories: {cats - expected_cats}")


# ============================================================
# 4. ProjectCustomerUser methods
# ============================================================

class ProjectCustomerUserMethodTests(TestCase):

    def setUp(self):
        self.customer = ProjectCustomer.objects.create(name='TestCorp')
        self.group = SystemGroup.objects.create(
            code='managers', name='Managers',
            object_permissions={
                'admin.customers': ['view', 'edit'],
                'ai.debug': ['manage'],
            }
        )
        self.user = ProjectCustomerUser.objects.create(
            customer=self.customer,
            login='testuser',
            first_name='Test',
            last_name='User',
        )
        self.user.system_groups.add(self.group)
        # Add org role with section
        self.section = SiteSection.objects.filter(
            code='catalog_gearbox', is_active=True
        ).first()
        self.role = Role.objects.create(
            customer=self.customer, code='engineer', name='Engineer'
        )
        self.role.section_permissions.add(self.section)
        self.user.roles.add(self.role)

    def test_has_system_perm_positive(self):
        self.assertTrue(self.user.has_system_perm('admin.customers', 'view'))
        self.assertTrue(self.user.has_system_perm('admin.customers', 'edit'))
        self.assertFalse(self.user.has_system_perm('admin.customers', 'delete'))

    def test_has_system_perm_manage(self):
        """manage action grants all actions."""
        self.assertTrue(self.user.has_system_perm('ai.debug', 'view'))
        self.assertTrue(self.user.has_system_perm('ai.debug', 'edit'))
        self.assertTrue(self.user.has_system_perm('ai.debug', 'delete'))

    def test_has_system_perm_unknown_object(self):
        """Unknown codename returns False (no permissions)."""
        self.assertFalse(self.user.has_system_perm('nonexistent.thing', 'view'))

    def test_has_system_perm_no_groups(self):
        """User without groups has no system perms."""
        self.user.system_groups.clear()
        self.assertFalse(self.user.has_system_perm('admin.customers', 'view'))

    def test_get_object_permissions(self):
        perms = self.user.get_object_permissions()
        self.assertIn('admin.customers', perms)
        self.assertIn('view', perms['admin.customers'])
        self.assertIn('edit', perms['admin.customers'])
        self.assertIn('ai.debug', perms)
        # manage expands to list containing 'manage'
        self.assertIn('manage', perms['ai.debug'])

    def test_get_effective_section_permissions(self):
        sections = self.user.get_effective_section_permissions()
        self.assertIn(self.section, sections)

    def test_system_groups_related_name(self):
        """members related_name works."""
        self.assertIn(self.user, self.group.members.all())


# ============================================================
# 5. DRF permission classes
# ============================================================

class SystemObjectPermissionTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.customer = ProjectCustomer.objects.create(name='PermCorp')
        self.group = SystemGroup.objects.create(
            code='editors', name='Editors',
            object_permissions={'admin.media': ['view', 'edit']}
        )
        self.profile = ProjectCustomerUser.objects.create(
            customer=self.customer, login='editor', first_name='Ed', last_name='Tor'
        )
        self.profile.system_groups.add(self.group)

    def _make_view(self, required_object=None, required_action='view'):
        class MockView:
            pass
        view = MockView()
        view.required_object = required_object
        view.required_action = required_action
        return view

    def _make_request(self, user=None):
        req = self.factory.get('/')
        req.user = user or AnonymousUser()
        if hasattr(user, 'is_authenticated') and user.is_authenticated:
            req.session = {'customer_user_id': self.profile.id}
        return req

    def test_no_required_object(self):
        """Endpoint without required_object passes."""
        perm = SystemObjectPermission()
        view = self._make_view(required_object=None)
        req = self._make_request(AnonymousUser())
        self.assertTrue(perm.has_permission(req, view))

    def test_anonymous_denied(self):
        perm = SystemObjectPermission()
        view = self._make_view(required_object='admin.media')
        req = self._make_request(AnonymousUser())
        self.assertFalse(perm.has_permission(req, view))

    def test_superuser_allowed(self):
        perm = SystemObjectPermission()
        view = self._make_view(required_object='admin.media')
        su = User.objects.create_superuser('su', 'su@test.com', 'pass')
        req = self._make_request(su)
        self.assertTrue(perm.has_permission(req, view))

    def test_has_permission_allowed(self):
        perm = SystemObjectPermission()
        view = self._make_view(required_object='admin.media', required_action='view')
        django_user = User.objects.create_user('editor_dj', password='pass')
        self.profile.user = django_user
        self.profile.save()
        req = self._make_request(django_user)
        req.session['customer_user_id'] = self.profile.id
        self.assertTrue(perm.has_permission(req, view))

    def test_has_permission_denied_action(self):
        perm = SystemObjectPermission()
        view = self._make_view(required_object='admin.media', required_action='delete')
        django_user = User.objects.create_user('editor2', password='pass')
        self.profile.user = django_user
        self.profile.save()
        req = self._make_request(django_user)
        req.session['customer_user_id'] = self.profile.id
        self.assertFalse(perm.has_permission(req, view))


class OrgSectionPermissionTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.customer = ProjectCustomer.objects.create(name='OrgCorp')
        self.section = SiteSection.objects.filter(
            code='catalog_gearbox', is_active=True
        ).first()
        self.role = Role.objects.create(
            customer=self.customer, code='viewer', name='Viewer'
        )
        self.role.section_permissions.add(self.section)
        self.profile = ProjectCustomerUser.objects.create(
            customer=self.customer, login='viewer', first_name='V', last_name='W'
        )
        self.profile.roles.add(self.role)

    def _make_view(self, required_section=None, public=False):
        class MockView:
            pass
        view = MockView()
        view.required_section = required_section
        view.public = public
        return view

    def _make_request(self, user=None):
        req = self.factory.get('/')
        req.user = user or AnonymousUser()
        if hasattr(user, 'is_authenticated') and user.is_authenticated:
            req.session = {'customer_user_id': self.profile.id}
        return req

    def test_public_allowed(self):
        perm = OrgSectionPermission()
        view = self._make_view(public=True)
        req = self._make_request(AnonymousUser())
        self.assertTrue(perm.has_permission(req, view))

    def test_anonymous_denied(self):
        perm = OrgSectionPermission()
        view = self._make_view(required_section='catalog_gearbox')
        req = self._make_request(AnonymousUser())
        self.assertFalse(perm.has_permission(req, view))

    def test_superuser_allowed(self):
        perm = OrgSectionPermission()
        view = self._make_view(required_section='catalog_gearbox')
        su = User.objects.create_superuser('su_org', 'su@o.com', 'pass')
        req = self._make_request(su)
        self.assertTrue(perm.has_permission(req, view))

    def test_has_section_allowed(self):
        perm = OrgSectionPermission()
        view = self._make_view(required_section='catalog_gearbox')
        django_user = User.objects.create_user('viewer_dj', password='pass')
        self.profile.user = django_user
        self.profile.save()
        req = self._make_request(django_user)
        req.session['customer_user_id'] = self.profile.id
        self.assertTrue(perm.has_permission(req, view))

    def test_has_section_denied(self):
        perm = OrgSectionPermission()
        view = self._make_view(required_section='configurator_pa')
        django_user = User.objects.create_user('viewer2', password='pass')
        self.profile.user = django_user
        self.profile.save()
        req = self._make_request(django_user)
        req.session['customer_user_id'] = self.profile.id
        self.assertFalse(perm.has_permission(req, view))

    def test_no_required_section_passes(self):
        perm = OrgSectionPermission()
        view = self._make_view(required_section=None)
        req = self._make_request(AnonymousUser())
        self.assertTrue(perm.has_permission(req, view))


# ============================================================
# 6. /auth/me/ API response
# ============================================================

class AuthMeResponseTests(TestCase):

    def setUp(self):
        self.customer = ProjectCustomer.objects.create(name='AuthCorp')
        self.group = SystemGroup.objects.create(
            code='staff', name='Staff',
            object_permissions={'admin.customers': ['view']}
        )
        self.profile = ProjectCustomerUser.objects.create(
            customer=self.customer,
            login='staffer',
            first_name='Staff', last_name='Member',
            email='staff@test.com',
        )
        self.profile.system_groups.add(self.group)
        self.django_user = User.objects.create_user('staff_dj', password='pass')
        self.profile.user = self.django_user
        self.profile.save()

    def test_auth_me_returns_system_groups(self):
        self.client.force_login(self.django_user)
        session = self.client.session
        session['customer_user_id'] = self.profile.id
        session.save()
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('system_groups', data)
        self.assertIn('staff', data['system_groups'])
        self.assertIn('object_permissions', data)
        self.assertIn('admin.customers', data['object_permissions'])
        self.assertIn('section_permissions', data)
        self.assertEqual(data['customer'], 'AuthCorp')

    def test_auth_me_unauthenticated(self):
        resp = self.client.get('/api/auth/me/')
        self.assertIn(resp.status_code, [401, 403],
            f"Expected 401/403, got {resp.status_code}")


# ============================================================
# 7. Admin API endpoints
# ============================================================

class AdminAPIEndpointTests(TestCase):

    def setUp(self):
        self.su = User.objects.create_superuser('admin', 'admin@t.com', 'pass')
        self.customer = ProjectCustomer.objects.create(name='APICorp')
        self.group = SystemGroup.objects.create(
            code='api_group', name='API Group',
            object_permissions={'admin.customers': ['view']}
        )
        self.profile = ProjectCustomerUser.objects.create(
            customer=self.customer, login='apiuser',
            first_name='API', last_name='User',
        )
        self.profile.system_groups.add(self.group)
        self.profile.user = User.objects.create_user('api_dj', password='pass')
        self.profile.save()

    def test_object_registry_api(self):
        self.client.force_login(self.su)
        resp = self.client.get('/api/admin/object-registry/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('objects', data)
        self.assertGreater(len(data['objects']), 15)

    def test_system_groups_list_api(self):
        self.client.force_login(self.su)
        resp = self.client.get('/api/admin/system-groups/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('groups', data)
        self.assertGreaterEqual(len(data['groups']), 1)
        group = data['groups'][0]
        self.assertIn('code', group)
        self.assertIn('object_permissions', group)
        self.assertIn('user_count', group)

    def test_site_sections_list_api(self):
        self.client.force_login(self.su)
        resp = self.client.get('/api/admin/site-sections/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('sections', data)
        self.assertGreaterEqual(len(data['sections']), 17)
        codes = [s['code'] for s in data['sections']]
        self.assertIn('catalog_gearbox', codes)
        self.assertIn('configurator_pa', codes)

    def test_system_groups_update(self):
        self.client.force_login(self.su)
        resp = self.client.put(
            f'/api/admin/system-groups/{self.group.id}/',
            {'object_permissions': {'admin.customers': ['view', 'edit']}},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('view', data['object_permissions']['admin.customers'])
        self.assertIn('edit', data['object_permissions']['admin.customers'])
