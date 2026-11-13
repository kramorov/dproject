# core/tests/test_template_field_registry.py
"""Тесты реестра полей шаблонов EquipmentType."""

from django.test import TestCase


class TemplateFieldRegistryTests(TestCase):
    def test_electric_actuator_override_resolves_catalog_fields(self):
        """electric-actuator → ElectricActuatorCatalogItem (мост для stale content_type)."""
        from django.apps import apps
        from core.template_field_registry import (
            _EQUIPMENT_TYPE_MODEL_OVERRIDES,
            collect_template_fields_for_model,
        )
        label = _EQUIPMENT_TYPE_MODEL_OVERRIDES['electric-actuator']
        model = apps.get_model(*label.split('.'))
        specs = collect_template_fields_for_model(model)
        self.assertTrue(specs)
        ph = {s.placeholder for s in specs}
        self.assertIn('{model_code}', ph)
        self.assertIn('{cu_block}', ph)
        self.assertIn('{cu_code}', ph)
        self.assertIn('{cu_description}', ph)
