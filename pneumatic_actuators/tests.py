"""
Tests for pneumatic_actuators SKU service (переработаны 2026-09-01).

SKU теперь создаётся из эталонной модели PneumaticActuatorItem
(через SKUMixin.sync_sku()), а не как standalone-запись.
"""
from django.test import TestCase

from pneumatic_actuators.services.sku_service import get_or_create_sku


class GetOrCreateSkuTests(TestCase):

    def setUp(self):
        from core.models.equipment_type import EquipmentType
        from producers.models import Brands
        from pneumatic_actuators.models import (
            PneumaticActuatorModelLine,
            PneumaticActuatorModelLineItem,
        )

        self.equipment_type = EquipmentType.objects.create(
            name='Пневмопривод', code='PA', level=1,
        )
        self.brand = Brands.objects.create(name='TestBrand', code='TB')
        self.model_line = PneumaticActuatorModelLine.objects.create(
            name='Test Series', code='TS',
            brand=self.brand,
            equipment_type=self.equipment_type,
        )
        self.item = PneumaticActuatorModelLineItem.objects.create(
            name='Test Item', code='TI-01',
            model_line=self.model_line,
            is_active=True,
        )

    def test_creates_sku_via_reference_model(self):
        from sku.models import SKU
        from pneumatic_actuators.models import PneumaticActuatorItem

        initial_count = SKU.objects.count()
        sku = get_or_create_sku(self.item, {})

        self.assertEqual(SKU.objects.count(), initial_count + 1)
        # fallback-код: из source-мостика (legacy item.code)
        self.assertEqual(sku.code, 'TI-01')
        self.assertEqual(sku.equipment_type, self.equipment_type)
        self.assertEqual(sku.brand, self.brand)
        self.assertEqual(sku.source_content_type.model_class(), PneumaticActuatorItem)

        item_row = PneumaticActuatorItem.objects.get(source_model_line_item=self.item)
        self.assertEqual(item_row.code, 'TI-01')
        self.assertEqual(item_row.sku, sku)

    def test_dedup_same_options(self):
        from sku.models import SKU

        sku1 = get_or_create_sku(self.item, {})
        count_after_first = SKU.objects.count()
        sku2 = get_or_create_sku(self.item, {})
        self.assertEqual(SKU.objects.count(), count_after_first)
        self.assertEqual(sku1.id, sku2.id)

    def test_option_encoding_in_code(self):
        from pneumatic_actuators.models import PneumaticActuatorSpringsQty
        from pneumatic_actuators.models.pa_options import PneumaticSpringsQtyOption

        springs12 = PneumaticActuatorSpringsQty.objects.create(name='12 пружин', code='SP12')
        springs8 = PneumaticActuatorSpringsQty.objects.create(name='8 пружин', code='SP8')
        PneumaticSpringsQtyOption.objects.create(
            model_line_item=self.item, springs_qty=springs12, encoding='12', is_default=True,
        )
        PneumaticSpringsQtyOption.objects.create(
            model_line_item=self.item, springs_qty=springs8, encoding='8', is_default=False,
        )

        sku1 = get_or_create_sku(self.item, {'springs_qty': springs12.id})
        sku2 = get_or_create_sku(self.item, {'springs_qty': springs8.id})
        # fallback-код: bridge-код + encoding из through-модели
        self.assertEqual(sku1.code, 'TI-01.12')
        self.assertEqual(sku2.code, 'TI-01.8')
        self.assertNotEqual(sku1.id, sku2.id)

    def test_template_code_used_when_present(self):
        self.model_line.model_item_code_template = 'MOD.{model_code}.{springs_qty}'
        self.model_line.save(update_fields=['model_item_code_template'])

        sku = get_or_create_sku(self.item, {})
        # {springs_qty} пустой → хвостовая точка срезается очисткой
        self.assertEqual(sku.code, 'MOD.TI-01')

    def test_model_line_name_template_applied_to_sku_name(self):
        self.model_line.name_template = 'TPL {model_code}'
        self.model_line.description_template = 'TPL-D {model_code}'
        self.model_line.save(update_fields=['name_template', 'description_template'])

        sku = get_or_create_sku(self.item, {})
        self.assertTrue(sku.name.startswith('TPL TI-01'))
        self.assertEqual(sku.description, 'TPL-D TI-01')
