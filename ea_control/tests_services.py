# ea_control/tests_services.py
"""
Тесты сервисов фазы 3 (Паттерн А и В) — на данных сида seed_cu_demo.

Работают на копии рабочей БД (см. tests.py): сид выполняется в
setUpTestData; тесты не изменяют данные (только чтение резолверов).
"""
from django.core.management import call_command
from django.test import TestCase

from ea_control.models import ControlUnit
from ea_control.services.cu_matrix import (get_profile_defaults,
                                           resolve_control_units, resolve_slots,
                                           validate_selection)
from ea_control.services.cu_package import build_package
from ea_control.services.cu_rules import apply_rules


def _flatten(resolved):
    return [p for slot_payloads in resolved.values() for p in slot_payloads]


class CuMatrixServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_cu_demo')
        from electric_actuators.models import ElectricActuatorModelLine
        from params.models import PowerSupplies
        cls.ar01e = ElectricActuatorModelLine.objects.get(code='AR01E')
        cls.ar11e = ElectricActuatorModelLine.objects.get(code='AR11E')
        cls.ps380 = PowerSupplies.objects.get(code='380-AC')
        cls.ps24 = PowerSupplies.objects.get(code='24-DC')
        cls.basic = ControlUnit.objects.get(code='basic')
        cls.int_unit = ControlUnit.objects.get(code='int-n')
        cls.int_mb = ControlUnit.objects.get(code='int-n-mb')
        cls.posi = ControlUnit.objects.get(code='posi-4-20')

    def test_resolve_slots_basic(self):
        resolved = resolve_slots(self.basic)
        self.assertIn('LOCAL_CONTROL', resolved)
        self.assertIn('HEATER_CONTROL_UNIT', resolved)
        # базовому шину не резолвим — строк нет
        self.assertNotIn('PROTOCOL', resolved)
        buttons = [p for p in resolved['LOCAL_CONTROL']]
        self.assertTrue(any(p['option_code'] == 'BUTTONS'
                            and p['availability'] == 'std' for p in buttons))

    def test_resolve_control_units_ar01e_380(self):
        units = resolve_control_units(self.ar01e, power_supply=self.ps380)
        codes = {u['code'] for u in units}
        self.assertIn('basic', codes)
        self.assertIn('int-n', codes)
        self.assertIn('int-n-mb', codes)
        self.assertNotIn('posi-4-20', codes)  # na-запрет на 380
        default = [u for u in units if u['is_default']]
        self.assertEqual([u['code'] for u in default], ['basic'])
        # option_code — код опции слота control_unit (для снимка/правил)
        self.assertEqual(default[0]['option_code'], 'CU_BASIC')

    def test_resolve_control_units_ar01e_24(self):
        units = resolve_control_units(self.ar01e, power_supply=self.ps24)
        codes = {u['code'] for u in units}
        self.assertIn('posi-4-20', codes)
        self.assertNotIn('basic', codes)  # для 24В базовый не описан

    def test_resolve_control_units_ar11e(self):
        units = resolve_control_units(self.ar11e, power_supply=self.ps380)
        codes = {u['code'] for u in units}
        self.assertEqual(codes, {'int-n'})  # у AR11E только INT
        self.assertTrue(units[0]['is_default'])

    def test_profile_defaults_int(self):
        defaults = get_profile_defaults(self.int_unit)
        self.assertEqual(defaults.get('INDICATOR'), 'LCD')
        self.assertEqual(defaults.get('POSITION_FEEDBACK'), 'POS_4_20_ACTIVE')

    def test_bundle_atomicity(self):
        resolved = resolve_slots(self.int_unit)
        available = _flatten(resolved)
        mwg = [p for p in available if p.get('bundle') == 'MWG']
        self.assertEqual(len(mwg), 3)
        # выбрана одна строка пакета — ошибка
        errors = validate_selection([mwg[0]], available)
        self.assertTrue(any('MWG' in e for e in errors))
        # выбран весь пакет — ок
        self.assertEqual(validate_selection(mwg, available), [])

    def test_conflicts(self):
        resolved = resolve_slots(self.int_unit)
        available = _flatten(resolved)
        mwg = next(p for p in available
                   if p['slot_code'] == 'POSITION_FEEDBACK'
                   and p['option_code'] == 'POS_MWG')
        torque = next(p for p in available
                      if p['slot_code'] == 'TORQUE_SWITCHES'
                      and p['option_code'] == 'TORQUE_SPDT')
        errors = validate_selection([mwg, torque], available)
        self.assertTrue(any('Конфликт' in e for e in errors))


class CuRulesServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_cu_demo')
        from ea_control.models import CuSlotRule
        cls.rules = CuSlotRule.objects.all()

    def test_basic_hides_protocol_and_setpoint(self):
        state = apply_rules(self.rules, {'control_unit': 'CU_BASIC'})
        self.assertFalse(state.get('PROTOCOL', {}).get('visible', True))
        self.assertFalse(state.get('SETPOINT', {}).get('visible', True))

    def test_int_mb_shows_protocol(self):
        state = apply_rules(self.rules, {'control_unit': 'CU_INT_MB'})
        self.assertTrue(state.get('PROTOCOL', {}).get('visible', True))

    def test_hart_set_default(self):
        state = apply_rules(self.rules, {'SETPOINT': 'SETPOINT_HART'})
        self.assertEqual(state['POSITION_FEEDBACK']['default'], 'POS_HART')


class CuPackageServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_cu_demo')
        from electric_actuators.models import ElectricActuatorModelLine
        from params.models import PowerSupplies
        cls.ar01e = ElectricActuatorModelLine.objects.get(code='AR01E')
        cls.ps380 = PowerSupplies.objects.get(code='380-AC')

    def test_build_package(self):
        unit = ControlUnit.objects.get(code='int-n')
        pkg = build_package(unit, model_line=self.ar01e, power_supply=self.ps380,
                            locale='ru')
        self.assertEqual(pkg['unit']['code'], 'int-n')
        self.assertTrue(pkg['unit']['name'])
        self.assertTrue(pkg['sections'])
        self.assertTrue(pkg['slots'])
        # слот PROTOCOL в пакете есть, но все опции недоступны (None)
        protocol = next(s for s in pkg['slots'] if s['code'] == 'PROTOCOL')
        self.assertTrue(all(o['availability'] is None for o in protocol['options']))
        # опции INDICATOR: LCD доступна как std
        indicator = next(s for s in pkg['slots'] if s['code'] == 'INDICATOR')
        lcd = next(o for o in indicator['options'] if o['code'] == 'LCD')
        self.assertEqual(lcd['availability'], 'std')
        self.assertEqual(pkg['defaults'].get('INDICATOR'), 'LCD')
        self.assertTrue(pkg['rules'])
