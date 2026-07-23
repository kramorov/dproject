"""
Tests for authentication: CustomerBackend, LoginView, CurrentUserView, API keys.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from project_customers.models import (
    ProjectCustomer, ProjectCustomerUser, Role, SiteSection,
    AllowedApp, CustomerApiKey,
)


class AuthenticationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # --- Customer ---
        cls.customer = ProjectCustomer.objects.create(name='TestOrg', is_active=True)

        # --- SiteSections ---
        cls.catalog = SiteSection.objects.create(code='catalog', name='Catalog', is_active=True)
        cls.config = SiteSection.objects.create(code='configurator', name='Configurator', is_active=True)
        cls.requests = SiteSection.objects.create(code='requests', name='Requests', is_active=True)
        cls.certs = SiteSection.objects.create(code='certificates', name='Certificates', is_active=True)
        cls.llm = SiteSection.objects.create(code='llm_agent', name='LLM Agent', is_active=True)
        all_sections = [cls.catalog, cls.config, cls.requests, cls.certs, cls.llm]
        site_sections = [cls.catalog, cls.config, cls.requests, cls.certs]

        # --- Django Users (shared per role) ---
        cls.api_dj_user = User.objects.create_user(username='role_api', is_active=True, is_staff=False)
        cls.site_dj_user = User.objects.create_user(username='role_site', is_active=True, is_staff=False)
        cls.admin_dj_user = User.objects.create_user(username='role_admin', is_active=True, is_staff=False)

        # --- Roles ---
        cls.api_role = Role.objects.create(
            customer=cls.customer, code='api_user', name='API User',
            django_user=cls.api_dj_user,
        )
        cls.api_role.section_permissions.set([])

        cls.site_role = Role.objects.create(
            customer=cls.customer, code='site_user', name='Site User',
            django_user=cls.site_dj_user, is_default=True,
        )
        cls.site_role.section_permissions.set(site_sections)

        cls.admin_role = Role.objects.create(
            customer=cls.customer, code='system_admin', name='System Admin',
            django_user=cls.admin_dj_user,
        )
        cls.admin_role.section_permissions.set(all_sections)

        # --- ProjectCustomerUsers ---
        cls.api_user = ProjectCustomerUser.objects.create(
            customer=cls.customer, email='api@test.com',
            first_name='API', last_name='User', is_active=True,
        )
        cls.api_user.set_password('test123')
        cls.api_user.roles.add(cls.api_role)
        cls.api_user.save()

        cls.site_user = ProjectCustomerUser.objects.create(
            customer=cls.customer, email='site@test.com',
            first_name='Site', last_name='User', is_active=True,
        )
        cls.site_user.set_password('test123')
        cls.site_user.roles.add(cls.site_role)
        cls.site_user.save()

        cls.admin_user = ProjectCustomerUser.objects.create(
            customer=cls.customer, email='admin@test.com',
            first_name='Admin', last_name='User', is_active=True,
        )
        cls.admin_user.set_password('test123')
        cls.admin_user.roles.add(cls.admin_role)
        cls.admin_user.save()

        # --- Inactive user ---
        cls.inactive_user = ProjectCustomerUser.objects.create(
            customer=cls.customer, email='inactive@test.com',
            first_name='Inactive', last_name='User', is_active=False,
        )
        cls.inactive_user.set_password('test123')
        cls.inactive_user.roles.add(cls.site_role)
        cls.inactive_user.save()

        # --- No-role user (no django_user on role) ---
        cls.no_role_role = Role.objects.create(
            customer=cls.customer, code='no_dj', name='No Django',
            django_user=None,
        )
        cls.no_role_user = ProjectCustomerUser.objects.create(
            customer=cls.customer, email='norole@test.com',
            first_name='No', last_name='Role', is_active=True,
        )
        cls.no_role_user.set_password('test123')
        cls.no_role_user.roles.add(cls.no_role_role)
        cls.no_role_user.save()

        cls.client = Client()

    # --- Login tests ---

    def test_api_user_login(self):
        resp = self.client.post('/api/auth/login/', {'email': 'api@test.com', 'password': 'test123'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('api_user', data['roles'])
        self.assertEqual(data['section_permissions'], [])
        self.assertEqual(data['customer'], 'TestOrg')
        self.assertIn('customer_user_id', self.client.session)

    def test_site_user_login(self):
        resp = self.client.post('/api/auth/login/', {'email': 'site@test.com', 'password': 'test123'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('site_user', data['roles'])
        self.assertIn('catalog', data['section_permissions'])
        self.assertIn('configurator', data['section_permissions'])
        self.assertNotIn('llm_agent', data['section_permissions'])

    def test_admin_user_login(self):
        resp = self.client.post('/api/auth/login/', {'email': 'admin@test.com', 'password': 'test123'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('system_admin', data['roles'])
        self.assertIn('llm_agent', data['section_permissions'])

    def test_wrong_password(self):
        resp = self.client.post('/api/auth/login/', {'email': 'site@test.com', 'password': 'wrong'}, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.json())

    def test_inactive_user(self):
        resp = self.client.post('/api/auth/login/', {'email': 'inactive@test.com', 'password': 'test123'}, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_nonexistent_email(self):
        resp = self.client.post('/api/auth/login/', {'email': 'nobody@test.com', 'password': 'test123'}, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_no_django_user_on_role(self):
        resp = self.client.post('/api/auth/login/', {'email': 'norole@test.com', 'password': 'test123'}, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_missing_fields(self):
        resp = self.client.post('/api/auth/login/', {}, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Email и пароль обязательны', resp.json()['error'])

    # --- CurrentUser tests ---

    def test_current_user_after_login(self):
        self.client.post('/api/auth/login/', {'email': 'site@test.com', 'password': 'test123'}, content_type='application/json')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['username'], 'Site User')
        self.assertIn('site_user', data['roles'])

    def test_current_user_not_authenticated(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 403)

    # --- Logout tests ---

    def test_logout_clears_session(self):
        self.client.post('/api/auth/login/', {'email': 'site@test.com', 'password': 'test123'}, content_type='application/json')
        self.assertIn('customer_user_id', self.client.session)
        resp = self.client.post('/api/auth/logout/')
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('customer_user_id', self.client.session)

    # --- Superuser tests ---

    def test_superuser_login_by_username(self):
        User.objects.create_superuser(username='admin', email='a@a.com', password='admin123')
        resp = self.client.post('/api/auth/login/',
            {'email': 'admin', 'password': 'admin123'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('admin', data['roles'])
        self.assertIn('llm_agent', data['section_permissions'])

    # --- API keys ---

    def setUp(self):
        self.client = Client()

    def test_create_api_key(self):
        self.client.post('/api/auth/login/', {'email': 'admin@test.com', 'password': 'test123'}, content_type='application/json')
        resp = self.client.post('/api/auth/api-keys/',
            {'name': 'Test Key', 'allowed_apps': ['llm_agent']}, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn('raw_key', data)
        self.assertTrue(data['raw_key'].startswith('proj_live_'))
        self.assertIn('llm_agent', data['allowed_apps'])
        self.assertIn('warning', data)

    def test_list_api_keys(self):
        self.client.post('/api/auth/login/', {'email': 'admin@test.com', 'password': 'test123'}, content_type='application/json')
        # Create a key first
        self.client.post('/api/auth/api-keys/', {'name': 'K1'}, content_type='application/json')
        resp = self.client.get('/api/auth/api-keys/')
        self.assertEqual(resp.status_code, 200)
        keys = resp.json()['keys']
        self.assertGreaterEqual(len(keys), 1)
        self.assertNotIn('raw_key', keys[0])

    def test_revoke_api_key(self):
        self.client.post('/api/auth/login/', {'email': 'admin@test.com', 'password': 'test123'}, content_type='application/json')
        create_resp = self.client.post('/api/auth/api-keys/', {'name': 'ToRevoke'}, content_type='application/json')
        key_id = create_resp.json()['id']

        resp = self.client.delete(f'/api/auth/api-keys/{key_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['is_active'])

    def test_api_key_lookup(self):
        instance = CustomerApiKey.objects.create(
            customer=self.customer, name='LookupTest',
            key_prefix='proj_live_', is_active=True,
        )
        raw = 'proj_live_testlookupkey1234'
        import hashlib
        instance.key_hash = hashlib.sha256(raw.encode()).hexdigest()
        instance.save()

        found = CustomerApiKey.lookup(raw)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, 'LookupTest')

        not_found = CustomerApiKey.lookup('nonexistent_key_12345678')
        self.assertIsNone(not_found)
