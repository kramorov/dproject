"""
Tests for pneumatic_actuators SKU service and CatalogDictMixin.
"""
from django.test import TestCase

from pneumatic_actuators.services.sku_service import (
    _safe_code, build_pa_sku_code, build_pa_sku_name, get_or_create_sku,
)


# ═══════════════════════════════════════════════════════════════════
# _safe_code unit tests
# ═══════════════════════════════════════════════════════════════════

class SafeCodeTests(TestCase):

    def test_none_returns_empty_string(self):
        self.assertEqual(_safe_code(None), '')

    def test_int_returns_str(self):
        self.assertEqual(_safe_code(12), '12')
        self.assertEqual(_safe_code(0), '0')
        self.assertEqual(_safe_code(-5), '-5')

    def test_float_returns_str(self):
        self.assertEqual(_safe_code(3.14), '3.14')

    def test_string_returns_string(self):
        self.assertEqual(_safe_code('hello'), 'hello')

    def test_object_with_encoding(self):
        class Opt:
            encoding = 'NC'
            code = 'nc'
        self.assertEqual(_safe_code(Opt()), 'NC')

    def test_object_with_code_only(self):
        class Opt:
            code = 'IP67'
        self.assertEqual(_safe_code(Opt()), 'IP67')

    def test_object_with_name_only(self):
        class Opt:
            name = 'Standard'
        self.assertEqual(_safe_code(Opt()), 'Standard')

    def test_plain_object_returns_str(self):
        class Unknown:
            pass
        s = _safe_code(Unknown())
        self.assertIn('Unknown', s)

    def test_empty_encoding_uses_code(self):
        class Opt:
            encoding = ''
            code = 'DA'
        self.assertEqual(_safe_code(Opt()), 'DA')


# ═══════════════════════════════════════════════════════════════════
# build_pa_sku_code tests
# ═══════════════════════════════════════════════════════════════════

class BuildPaSkuCodeTests(TestCase):

    def setUp(self):
        # Mock model_line_item
        class FakeItem:
            code = 'PA52SR20'
            name = 'PA52SR20 Name'
        self.item = FakeItem()

    def test_no_options_returns_item_code(self):
        code = build_pa_sku_code(self.item, {})
        self.assertEqual(code, 'PA52SR20')

    def test_with_int_options(self):
        code = build_pa_sku_code(self.item, {
            'springs_qty': 12,
            'temperature': 3,
            'ip': 1,
        })
        self.assertEqual(code, 'PA52SR20-12-3-1')

    def test_with_string_options(self):
        code = build_pa_sku_code(self.item, {
            'springs_qty': '12',
            'ip': 'IP67',
            'exd': 'ExdIICT6',
        })
        self.assertEqual(code, 'PA52SR20-12-IP67-ExdIICT6')

    def test_skips_none_values(self):
        code = build_pa_sku_code(self.item, {
            'springs_qty': 12,
            'temperature': None,
            'ip': 'IP67',
        })
        self.assertEqual(code, 'PA52SR20-12-IP67')

    def test_falls_back_to_name_when_no_code(self):
        class FakeItemNoCode:
            code = None
            name = 'PA52SR20 Name'
        code = build_pa_sku_code(FakeItemNoCode(), {'ip': 'IP67'})
        self.assertEqual(code, 'PA52SR20 Name-IP67')


# ═══════════════════════════════════════════════════════════════════
# build_pa_sku_name tests
# ═══════════════════════════════════════════════════════════════════

class BuildPaSkuNameTests(TestCase):

    def setUp(self):
        class FakeVariety:
            name = 'SR'
        class FakeBody:
            torque_at_6bar = 200
            weight = 15
        class FakeModelLine:
            pass
        class FakeItem:
            code = 'PA52SR20'
            name = 'PA52SR20'
            model_line = FakeModelLine()
            body = FakeBody()
            pneumatic_actuator_variety = FakeVariety()
        self.item = FakeItem()

    def test_basic_name_with_variety_and_torque(self):
        name = build_pa_sku_name(self.item, {'springs_qty': 12})
        self.assertIn('PA52SR20', name)
        self.assertIn('SR', name)
        self.assertIn('200 Нм', name)
        self.assertIn('12', name)

    def test_name_without_body(self):
        class FakeItemNoBody:
            code = 'PA52SR20'
            name = 'PA52SR20'
            model_line = None
            body = None
            pneumatic_actuator_variety = None
        name = build_pa_sku_name(FakeItemNoBody(), {})
        self.assertEqual(name, 'PA52SR20')

    def test_name_includes_all_option_labels(self):
        name = build_pa_sku_name(self.item, {
            'springs_qty': 12,
            'temperature': 'Low',
            'ip': 'IP67',
        })
        self.assertIn('пружин 12', name.lower())
        self.assertIn('IP67', name)


# ═══════════════════════════════════════════════════════════════════
# get_or_create_sku integration test
# ═══════════════════════════════════════════════════════════════════

class GetOrCreateSkuTests(TestCase):

    def setUp(self):
        from core.models.equipment_type import EquipmentType
        from producers.models import Brands
        from pneumatic_actuators.models import (
            PneumaticActuatorModelLine,
            PneumaticActuatorModelLineItem,
        )

        # Create minimal EquipmentType
        self.equipment_type = EquipmentType.objects.create(
            name='Пневмопривод', code='PA', level=1,
        )

        # Create brand
        self.brand = Brands.objects.create(name='TestBrand', code='TB')

        # Create model line
        self.model_line = PneumaticActuatorModelLine.objects.create(
            name='Test Series', code='TS',
            brand=self.brand,
            equipment_type=self.equipment_type,
        )

        # Create model line item (minimal)
        self.item = PneumaticActuatorModelLineItem.objects.create(
            name='Test Item', code='TI-01',
            model_line=self.model_line,
            is_active=True,
        )

    def test_creates_sku_first_time(self):
        from sku.models.sku import SKU
        initial_count = SKU.objects.count()
        sku = get_or_create_sku(self.item, {'springs_qty': 12, 'ip': 'IP67'})
        self.assertEqual(SKU.objects.count(), initial_count + 1)
        self.assertTrue(sku.code.startswith('TI-01'))
        self.assertIn('IP67', sku.code)
        self.assertEqual(sku.equipment_type, self.equipment_type)
        self.assertEqual(sku.brand, self.brand)
        self.assertTrue(sku.is_active)

    def test_returns_existing_sku_on_duplicate(self):
        from sku.models.sku import SKU
        sku1 = get_or_create_sku(self.item, {'springs_qty': 8})
        count_after_first = SKU.objects.count()
        sku2 = get_or_create_sku(self.item, {'springs_qty': 8})
        self.assertEqual(SKU.objects.count(), count_after_first)
        self.assertEqual(sku1.id, sku2.id)

    def test_different_options_create_different_skus(self):
        from sku.models.sku import SKU
        sku1 = get_or_create_sku(self.item, {'springs_qty': 12})
        sku2 = get_or_create_sku(self.item, {'springs_qty': 8})
        self.assertNotEqual(sku1.code, sku2.code)
        self.assertNotEqual(sku1.id, sku2.id)
