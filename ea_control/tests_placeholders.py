# ea_control/tests_placeholders.py
"""
Тесты резолвера плейсхолдеров описания БУ (cu_placeholders).

Покрытие: {slot:}/{opt:}/{node:}, пустые/скрытые слоты пропускаются,
снимок перекрывает std-дефолт. Тесты гоняются на копии рабочей БД
(см. ea_control/tests.py, шапка).
"""
from django.test import TestCase

from ea_control.models import (ControlUnit, ControlUnitKind, CuMatrixEntry,
                               CuSectionNode, CuSlot, CuSlotOption)
from ea_control.services.cu_placeholders import render_placeholders


class PlaceholderResolverTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from producers.models import Brands

        cls.brand = Brands.objects.first()
        cls.kind = ControlUnitKind.objects.get_or_create(
            code='PH_TEST_KIND', defaults=dict(name='Тест'))[0]
        cls.unit = ControlUnit.objects.create(
            brand=cls.brand, code='PH-TEST', name='PH Test', kind=cls.kind)

        cls.node = CuSectionNode.objects.create(
            code='PH_NODE', name='Node', placeholder='node1')

        cls.slot = CuSlot.objects.create(
            code='PH_SLOT', name='Slot', section=cls.node,
            slot_kind='value', placeholder='slot1')
        cls.slot2 = CuSlot.objects.create(
            code='PH_SLOT2', name='Slot2', section=cls.node,
            slot_kind='value', placeholder='slot2')

        cls.opt = CuSlotOption.objects.create(
            code='PH_OPT', name='Opt', slot=cls.slot, kind='value',
            description='Desc1', placeholder='opt1')
        cls.opt2 = CuSlotOption.objects.create(
            code='PH_OPT2', name='Opt2', slot=cls.slot, kind='value',
            description='Desc2')

        # профильный std → PH_OPT предвыбран по умолчанию
        CuMatrixEntry.objects.create(
            slot=cls.slot, option=cls.opt, control_unit=cls.unit,
            availability='std')

    def test_slot_resolves_default_description(self):
        self.assertEqual(
            render_placeholders('{slot:slot1}', self.unit), 'Desc1')

    def test_slot_snapshot_overrides_default(self):
        self.assertEqual(
            render_placeholders('{slot:slot1}', self.unit,
                                snapshot={'PH_SLOT': 'PH_OPT2'}), 'Desc2')

    def test_slot_without_value_is_empty(self):
        self.assertEqual(
            render_placeholders('{slot:slot2}', self.unit), '')

    def test_opt_resolves_description(self):
        self.assertEqual(
            render_placeholders('{opt:opt1}', self.unit), 'Desc1')

    def test_node_renders_visible_slots_and_skips_empty(self):
        text = render_placeholders('{node:node1}', self.unit)
        self.assertIn('Slot: Desc1', text)
        self.assertNotIn('Slot2', text)

    def test_unknown_placeholder_is_empty(self):
        self.assertEqual(
            render_placeholders('{slot:missing}', self.unit), '')

    def test_description_hides_slot_without_value(self):
        """Слот без предвыбора (нет std/снимка) не попадает в описание/спеки."""
        from ea_control.services.cu_description import (build_description,
                                                        build_specification)
        text = build_description(self.unit)
        self.assertIn('Slot: Desc1', text)
        self.assertNotIn('Slot2', text)
        spec = build_specification(self.unit)
        codes = [s['code'] for sec in spec['sections'] for s in sec['slots']]
        self.assertEqual(codes, ['PH_SLOT'])

    def test_inline_placeholder(self):
        self.assertEqual(
            render_placeholders('Шина: {slot:slot1}', self.unit),
            'Шина: Desc1')

    def test_spec_and_description_respect_sorting_order(self):
        """Узлы/слоты/опции выводятся в порядке sorting_order (описание и спека)."""
        from ea_control.services.cu_description import (build_description,
                                                        build_specification)
        node_a = CuSectionNode.objects.create(
            code='ORD_A', name='NodeA', sorting_order=20)
        node_b = CuSectionNode.objects.create(
            code='ORD_B', name='NodeB', sorting_order=10)
        s_a = CuSlot.objects.create(code='ORD_A_S', name='AS', section=node_a,
                                    slot_kind='value', sorting_order=1)
        # в узле B два слота: BS0 (1) раньше BS1 (2)
        s_b0 = CuSlot.objects.create(code='ORD_B0', name='B0', section=node_b,
                                     slot_kind='value', sorting_order=1)
        s_b1 = CuSlot.objects.create(code='ORD_B1', name='B1', section=node_b,
                                     slot_kind='value', sorting_order=2)
        for s, code in ((s_a, 'ORD_A_O'), (s_b1, 'ORD_B1_O')):
            o = CuSlotOption.objects.create(code=code, name=code, slot=s,
                                            kind='value', description=code)
            CuMatrixEntry.objects.create(slot=s, option=o,
                                         control_unit=self.unit,
                                         availability='std')
        # в слоте B0 две опции: O1 (std, 1) раньше O2 (na, 2)
        o_b0_1 = CuSlotOption.objects.create(code='ORD_B0_O1', name='O1',
                                             slot=s_b0, kind='value',
                                             description='O1', sorting_order=1)
        o_b0_2 = CuSlotOption.objects.create(code='ORD_B0_O2', name='O2',
                                             slot=s_b0, kind='value',
                                             description='O2', sorting_order=2)
        CuMatrixEntry.objects.create(slot=s_b0, option=o_b0_1,
                                     control_unit=self.unit,
                                     availability='std')

        spec = build_specification(self.unit)
        codes = [sec['code'] for sec in spec['sections']]
        self.assertIn('ORD_A', codes)
        self.assertIn('ORD_B', codes)
        self.assertLess(codes.index('ORD_B'), codes.index('ORD_A'))

        sec_b = next(sec for sec in spec['sections'] if sec['code'] == 'ORD_B')
        self.assertEqual([s['code'] for s in sec_b['slots']],
                         ['ORD_B0', 'ORD_B1'])
        slot_b0 = next(s for s in sec_b['slots'] if s['code'] == 'ORD_B0')
        self.assertEqual([o['code'] for o in slot_b0['options']],
                         ['ORD_B0_O1', 'ORD_B0_O2'])

        text = build_description(self.unit)
        self.assertLess(text.index('NodeB'), text.index('NodeA'))

    def test_spec_respects_tree_order(self):
        """Depth-first: родитель идёт раньше детей (вложенность по parent)."""
        from ea_control.services.cu_description import build_specification
        parent = CuSectionNode.objects.create(
            code='ORD_P', name='PNode', sorting_order=100)
        child = CuSectionNode.objects.create(
            code='ORD_C', name='CNode', parent=parent, sorting_order=1)
        sp = CuSlot.objects.create(code='ORD_P_S', name='PS', section=parent,
                                   slot_kind='value')
        sc = CuSlot.objects.create(code='ORD_C_S', name='CS', section=child,
                                   slot_kind='value')
        for s, code in ((sp, 'ORD_P_O'), (sc, 'ORD_C_O')):
            o = CuSlotOption.objects.create(code=code, name=code, slot=s,
                                            kind='value', description=code)
            CuMatrixEntry.objects.create(slot=s, option=o,
                                         control_unit=self.unit,
                                         availability='std')

        spec = build_specification(self.unit)
        codes = [sec['code'] for sec in spec['sections']]
        # родитель (sorting_order=100) раньше ребёнка (sorting_order=1)
        self.assertIn('ORD_P', codes)
        self.assertIn('ORD_C', codes)
        self.assertLess(codes.index('ORD_P'), codes.index('ORD_C'))
