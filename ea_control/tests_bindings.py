# ea_control/tests_bindings.py
"""
РўРµСЃС‚С‹ РїСЂРёРІСЏР·РєРё Р‘РЈ Рє РјРѕРґРµР»СЏРј Р­Рџ (ControlUnitBinding).

РџРѕРєСЂС‹С‚РёРµ: РјРѕРґРµР»СЊ (СѓРЅРёРєР°Р»СЊРЅРѕСЃС‚СЊ, clean В«РјРѕРґРµР»СЊ Р±РµР· СЃРµСЂРёРёВ»), СЂРµР·РѕР»РІРµСЂС‹,
API (unit-bindings GET / unit-bindings/save PUT) Рё РєРѕРїРёСЂРѕРІР°РЅРёРµ Р‘РЈ СЃ
РїСЂРёРІСЏР·РєР°РјРё РїРѕ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЋ.

РўРµСЃС‚С‹ РіРѕРЅСЏСЋС‚СЃСЏ РЅР° РєРѕРїРёРё СЂР°Р±РѕС‡РµР№ Р‘Р” (СЃРј. ea_control/tests.py, С€Р°РїРєР°).
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APITestCase

from ea_control.models import (
    ControlUnit,
    ControlUnitBinding,
    resolve_bound_units,
    resolve_bound_unit_ids_for_series,
)


class ControlUnitBindingModelTests(TestCase):
    """РњРѕРґРµР»СЊ Рё СЂРµР·РѕР»РІРµСЂС‹ РїСЂРёРІСЏР·РєРё."""

    @classmethod
    def setUpTestData(cls):
        import unittest
        from electric_actuators.models import (
            ElectricActuatorModelLine,
            ElectricActuatorModelLineItem,
        )
        cls.line = ElectricActuatorModelLine.objects.get(code='AR01E')
        cls.items = list(cls.line.model_line_item_model_line.order_by('id')[:3])
        if len(cls.items) < 2:
            raise unittest.SkipTest('Р’ СЃРµСЂРёРё AR01E РјРµРЅСЊС€Рµ РґРІСѓС… РјРѕРґРµР»РµР№')
        cls.cu = ControlUnit.objects.get(code='BASIC-AR21')
        cls.other_cu = ControlUnit.objects.get(code='INT/N')

    def test_unique_cu_item(self):
        ControlUnitBinding.objects.create(
            control_unit=self.cu, model_line_item=self.items[0])
        with self.assertRaises(IntegrityError):
            ControlUnitBinding.objects.create(
                control_unit=self.cu, model_line_item=self.items[0])

    def test_clean_rejects_orphan_item(self):
        from electric_actuators.models import ElectricActuatorModelLineItem
        orphan = ElectricActuatorModelLineItem.objects.create(
            name='TestOrphan', model_line=None)
        b = ControlUnitBinding(control_unit=self.cu, model_line_item=orphan)
        with self.assertRaises(ValidationError):
            b.full_clean()

    def test_resolve_bound_units_for_item(self):
        ControlUnitBinding.objects.create(
            control_unit=self.cu, model_line_item=self.items[0])
        ControlUnitBinding.objects.create(
            control_unit=self.cu, model_line_item=self.items[1])
        ControlUnitBinding.objects.create(
            control_unit=self.other_cu, model_line_item=self.items[1])
        # РїСЂРёРІСЏР·РєР° Рє РґСЂСѓРіРѕРјСѓ item РЅРµ СЂРµР·РѕР»РІРёС‚СЃСЏ
        ids0 = {b.control_unit_id for b in resolve_bound_units(self.items[0])}
        self.assertIn(self.cu.id, ids0)
        self.assertNotIn(self.other_cu.id, ids0)
        ids = {b.control_unit_id for b in resolve_bound_units(self.items[1])}
        self.assertTrue({self.cu.id, self.other_cu.id} <= ids)

    def test_resolve_bound_unit_ids_for_series(self):
        ControlUnitBinding.objects.create(
            control_unit=self.cu, model_line_item=self.items[0])
        ids = set(resolve_bound_unit_ids_for_series(self.line))
        self.assertIn(self.cu.id, ids)

    def test_binding_model_line_property(self):
        b = ControlUnitBinding.objects.create(
            control_unit=self.cu, model_line_item=self.items[0])
        self.assertEqual(b.model_line.id, self.line.id)


class ControlUnitBindingApiTests(APITestCase):
    """unit-bindings/ Рё unit-bindings/save/ + РєРѕРїРёСЂРѕРІР°РЅРёРµ Р‘РЈ СЃ РїСЂРёРІСЏР·РєР°РјРё."""

    @classmethod
    def setUpTestData(cls):
        from electric_actuators.models import ElectricActuatorModelLine
        cls.user = get_user_model().objects.create_superuser(
            'cu-binding-tester', 'b@example.com', 'b')
        cls.line = ElectricActuatorModelLine.objects.get(code='AR01E')
        cls.items = list(cls.line.model_line_item_model_line.order_by('id')[:3])
        cls.cu = ControlUnit.objects.get(code='BASIC-AR21')

    def setUp(self):
        self.client.force_authenticate(self.user)

    def test_get_bindings_payload(self):
        r = self.client.get(
            '/api/ea-control/unit-bindings/', {'unit': self.cu.id})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn('bindings', r.data)
        self.assertIn('series', r.data)
        ar01 = next(s for s in r.data['series'] if s['code'] == 'AR01E')
        self.assertGreaterEqual(len(ar01['items']), 2)

    def test_save_full_replace(self):
        url = '/api/ea-control/unit-bindings/save/'
        r = self.client.put(url, {
            'unit': self.cu.id,
            'bindings': [
                {'model_line_item': self.items[0].id},
                {'model_line_item': self.items[1].id},
            ],
        }, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(
            ControlUnitBinding.objects.filter(control_unit=self.cu).count(), 2)

        # РїРѕРІС‚РѕСЂРЅР°СЏ Р·Р°РјРµРЅР° вЂ” РѕСЃС‚Р°С‘С‚СЃСЏ С‚РѕР»СЊРєРѕ РѕРґРЅР°
        r = self.client.put(url, {
            'unit': self.cu.id,
            'bindings': [{'model_line_item': self.items[2].id}],
        }, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        rows = list(ControlUnitBinding.objects.filter(control_unit=self.cu))
        self.assertEqual([x.model_line_item_id for x in rows],
                         [self.items[2].id])

    def test_save_rejects_orphan_item(self):
        from electric_actuators.models import ElectricActuatorModelLineItem
        orphan = ElectricActuatorModelLineItem.objects.create(
            name='TestOrphanApi', model_line=None)
        r = self.client.put('/api/ea-control/unit-bindings/save/', {
            'unit': self.cu.id,
            'bindings': [{'model_line_item': orphan.id}],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_copy_with_bindings(self):
        ControlUnitBinding.objects.create(
            control_unit=self.cu, model_line_item=self.items[0])
        r = self.client.post(
            f'/api/ea-control/control-units/{self.cu.id}/copy/',
            {'copy_bindings': True}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        new = ControlUnit.objects.get(pk=r.data['id'])
        self.assertEqual(
            list(new.bindings.values_list('model_line_item_id', flat=True)),
            [self.items[0].id])

    def test_copy_without_bindings(self):
        ControlUnitBinding.objects.create(
            control_unit=self.cu, model_line_item=self.items[0])
        r = self.client.post(
            f'/api/ea-control/control-units/{self.cu.id}/copy/',
            {'copy_bindings': False}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        new = ControlUnit.objects.get(pk=r.data['id'])
        self.assertEqual(new.bindings.count(), 0)

