"""
Tests for Selection Wizard API endpoints.

Usage: python manage.py test core.tests.test_wizard --verbosity=2
Or run directly: python _test_wizard.py
"""
import json, os, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django
django.setup()

from django.test import TestCase, Client
from django.contrib.contenttypes.models import ContentType
from core.models import EquipmentType, SelectionWizard
from core.wizard_filter_registry import WIZARD_FILTER_REGISTRY, get_filter_definitions_for_ct

# ── Test data ──
WIZARD_JSON = {
    "pages": [
        {"step_number": 1, "title": "Выберите серию", "description": "Шаг 1"},
        {"step_number": 2, "title": "Выберите IP", "description": "Шаг 2"},
    ],
    "filters": [
        {"param_name": "model_line_id", "page": 1, "order": 1, "label": "Серия", "default_value": None},
        {"param_name": "ip_id", "page": 2, "order": 1, "label": "IP", "default_value": None},
    ]
}


class WizardEndpointsTest(TestCase):
    """Test all wizard API endpoints."""

    def setUp(self):
        self.client = Client()
        # Get a test ET with a model that has FILTER_DEFINITIONS
        self.et_ls = EquipmentType.objects.get(id=8)  # LimitSwitchBox
        # Clean up any existing test wizards
        SelectionWizard.objects.filter(equipment_type=self.et_ls).delete()

    # ═══════════════════════════════════════════════════════════════
    # 1. Registry tests
    # ═══════════════════════════════════════════════════════════════

    def test_registry_has_gearbox(self):
        """GearBox (ct=275) should have filter defs from registry."""
        defs = get_filter_definitions_for_ct(275)
        self.assertIsNotNone(defs)
        self.assertGreater(len(defs), 0)
        self.assertEqual(defs[0].__class__.__name__, 'FilterDefinition')

    def test_registry_has_directionvalve(self):
        """DirectionValve (ct=227) should have filter defs from registry."""
        defs = get_filter_definitions_for_ct(227)
        self.assertIsNotNone(defs)
        self.assertGreater(len(defs), 0)

    def test_registry_has_filterregulator(self):
        """FilterRegulator (ct=270) should have filter defs from registry."""
        defs = get_filter_definitions_for_ct(270)
        self.assertIsNotNone(defs)
        self.assertGreater(len(defs), 0)

    def test_registry_limitswitchbox_returns_none(self):
        """LimitSwitchBox (ct=250) has FD on class, registry returns None."""
        defs = get_filter_definitions_for_ct(250)
        self.assertIsNone(defs)

    # ═══════════════════════════════════════════════════════════════
    # 2. Public endpoint: wizard config
    # ═══════════════════════════════════════════════════════════════

    def test_config_no_wizard(self):
        """GET /api/core/wizard/<id>/ without active wizard returns 404."""
        # Ensure no active wizard
        self.et_ls.active_selection_wizard = None
        self.et_ls.save()
        resp = self.client.get(f'/api/core/wizard/{self.et_ls.id}/')
        self.assertEqual(resp.status_code, 404)

    def test_config_with_wizard(self):
        """GET /api/core/wizard/<id>/ with active wizard returns config."""
        wizard = SelectionWizard.objects.create(
            name='Test Wizard', equipment_type=self.et_ls,
            steps_json=WIZARD_JSON
        )
        self.et_ls.active_selection_wizard = wizard
        self.et_ls.save()

        resp = self.client.get(f'/api/core/wizard/{self.et_ls.id}/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['wizard_name'], 'Test Wizard')
        self.assertEqual(data['total_steps'], 2)
        self.assertEqual(len(data['steps']), 2)
        self.assertEqual(data['steps'][0]['title'], 'Выберите серию')

    # ═══════════════════════════════════════════════════════════════
    # 3. Public endpoint: filter options
    # ═══════════════════════════════════════════════════════════════

    def test_filter_options_missing_param(self):
        """POST filter-options without param_name returns 400."""
        resp = self.client.post(
            f'/api/core/wizard/{self.et_ls.id}/filter-options/',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_filter_options_valid(self):
        """POST filter-options with valid param_name returns options with description."""
        wizard = SelectionWizard.objects.create(
            name='Test Wizard', equipment_type=self.et_ls,
            steps_json=WIZARD_JSON
        )
        self.et_ls.active_selection_wizard = wizard
        self.et_ls.save()

        resp = self.client.post(
            f'/api/core/wizard/{self.et_ls.id}/filter-options/',
            data=json.dumps({"param_name": "sensor_variety_id"}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('options', data)
        self.assertIn('param_name', data)

    def test_filter_options_bad_param(self):
        """POST filter-options with non-existent param_name returns 400."""
        wizard = SelectionWizard.objects.create(
            name='Test Wizard', equipment_type=self.et_ls,
            steps_json=WIZARD_JSON
        )
        self.et_ls.active_selection_wizard = wizard
        self.et_ls.save()

        resp = self.client.post(
            f'/api/core/wizard/{self.et_ls.id}/filter-options/',
            data=json.dumps({"param_name": "nonexistent_filter"}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    # ═══════════════════════════════════════════════════════════════
    # 4. Public endpoint: results
    # ═══════════════════════════════════════════════════════════════

    def test_results_no_model(self):
        """POST results with ET that has no model returns 400."""
        et = EquipmentType.objects.get(id=2)  # No content_type
        resp = self.client.post(
            f'/api/core/wizard/{et.id}/results/',
            data=json.dumps({"filters_applied": {}, "page": 1}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_results_pagination(self):
        """POST results returns paginated data."""
        wizard = SelectionWizard.objects.create(
            name='Test Wizard', equipment_type=self.et_ls,
            steps_json=WIZARD_JSON
        )
        self.et_ls.active_selection_wizard = wizard
        self.et_ls.save()

        resp = self.client.post(
            f'/api/core/wizard/{self.et_ls.id}/results/',
            data=json.dumps({"filters_applied": {}, "page": 1, "page_size": 5}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('items', data)
        self.assertIn('total', data)
        self.assertIn('page', data)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_size'], 5)

    # ═══════════════════════════════════════════════════════════════
    # 5. Public endpoint: model-filters
    # ═══════════════════════════════════════════════════════════════

    def test_model_filters_no_ct(self):
        """GET model-filters without content_type_id returns 400."""
        resp = self.client.get('/api/core/wizard/model-filters/')
        self.assertEqual(resp.status_code, 400)

    def test_model_filters_valid(self):
        """GET model-filters with valid content_type_id returns filters."""
        ct = ContentType.objects.get(app_label='pa_controls', model='limitswitchbox')
        resp = self.client.get(f'/api/core/wizard/model-filters/?content_type_id={ct.id}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('filters', data)
        self.assertGreater(len(data['filters']), 0)
        # Check that each filter has required fields
        for f in data['filters']:
            self.assertIn('param_name', f)
            self.assertIn('label', f)

    def test_model_filters_from_registry(self):
        """GET model-filters for GearBox (no FD on class) returns filters from registry."""
        ct = ContentType.objects.get(app_label='gearbox', model='gearbox')
        resp = self.client.get(f'/api/core/wizard/model-filters/?content_type_id={ct.id}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(len(data['filters']), 0)

    # ═══════════════════════════════════════════════════════════════
    # 6. Admin endpoints (require auth)
    # ═══════════════════════════════════════════════════════════════

    def test_admin_list_no_auth(self):
        """GET /api/core/wizard/admin/ without auth returns 401/403."""
        resp = self.client.get('/api/core/wizard/admin/')
        self.assertIn(resp.status_code, [401, 403])

    def test_admin_create_no_auth(self):
        """POST /api/core/wizard/admin/ without auth returns 401/403."""
        resp = self.client.post(
            '/api/core/wizard/admin/',
            data=json.dumps({'name': 'Test', 'equipment_type_id': self.et_ls.id}),
            content_type='application/json'
        )
        self.assertIn(resp.status_code, [401, 403])

    def test_admin_delete_no_auth(self):
        """DELETE /api/core/wizard/admin/<id>/ without auth returns 401/403."""
        wizard = SelectionWizard.objects.create(
            name='Test', equipment_type=self.et_ls, steps_json=WIZARD_JSON
        )
        resp = self.client.delete(f'/api/core/wizard/admin/{wizard.id}/')
        self.assertIn(resp.status_code, [401, 403])

    # ═══════════════════════════════════════════════════════════════
    # 7. Equipment types endpoint
    # ═══════════════════════════════════════════════════════════════

    def test_equipment_types_list_no_auth(self):
        """GET equipment-types without auth returns 401/403."""
        resp = self.client.get('/api/core/wizard/model-filters/equipment-types/')
        self.assertIn(resp.status_code, [401, 403])


if __name__ == '__main__':
    # Run tests directly
    import unittest
    suite = unittest.TestLoader().loadTestsFromTestCase(WizardEndpointsTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
