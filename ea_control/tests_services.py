# ea_control/tests_services.py
"""
Тесты сервисов фазы 3 (Паттерн А и В) — на данных сида seed_cu_demo.

Работают на копии рабочей БД (см. tests.py): сид выполняется в
setUpTestData; тесты не изменяют данные (только чтение резолверов).
"""
from django.core.management import call_command
from django.test import TestCase

from ea_control.models import (ControlUnit, CuControlSignal,
                               CuControlSignalForm, CuMatrixEntry,
                               CuSlot, CuSlotOption, CuSlotRule)
from ea_control.services.cu_matrix import (get_profile_defaults,
                                           resolve_control_units, resolve_slots,
                                           validate_selection)
from ea_control.services.cu_package import build_package
from ea_control.services.cu_rules import apply_rules
from ea_control.services.cu_unit_matrix import (MatrixValidationError,
                                                apply_unit_matrix_changes,
                                                apply_unit_rule_changes,
                                                build_unit_matrix)


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
        # схема цепей: внешняя 220 В std, внутренний +24 В опция
        wiring = resolved['CMD_WIRING']
        self.assertTrue(any(p['option_code'] == 'W_EXT_220'
                            and p['availability'] == 'std' for p in wiring))
        self.assertTrue(any(p['option_code'] == 'W_INT_24'
                            and p['availability'] == 'opt' for p in wiring))
        # стоп — отсутствием сигнала (опция «Отсутствие сигнала» std)
        stop = resolved['CMD_STOP']
        self.assertEqual([p['option_code'] for p in stop], ['CMD_STOP_NONE'])
        # AOX-M базовый: органов местного управления нет — только «Нет» (std)
        local = resolved['LOCAL_CONTROL']
        self.assertTrue(any(p['option_code'] == 'LOCAL_NONE'
                            and p['availability'] == 'std' for p in local))
        self.assertFalse(any(p['option_code'] == 'BUTTONS' for p in local))
        self.assertFalse(any(p['option_code'] == 'SELECTOR' for p in local))
        # обогрев — отдельной линией (std), от цепей питания — опция
        heater = resolved['HEATER_CONTROL_UNIT']
        self.assertTrue(any(p['option_code'] == 'H_SEP'
                            and p['availability'] == 'std' for p in heater))
        self.assertTrue(any(p['option_code'] == 'H_MOTOR'
                            and p['availability'] == 'opt' for p in heater))
        # стартера у базового нет — только «Нет» (std)
        starter = resolved['MOTOR_STARTER']
        self.assertTrue(any(p['option_code'] == 'STARTER_NONE' for p in starter))
        self.assertFalse(any(p['option_code'] == 'STARTER_BUILT_IN'
                             for p in starter))

    def test_signal_power_coordinate_posi(self):
        """Набор сигналов зависит от схемы цепей (координата signal_power)."""
        from ea_control.models import CuSignalPower
        ext_pnp = CuSignalPower.objects.get(name__startswith='Внешний 24 В DC (PNP)')
        without = resolve_slots(self.posi)
        self.assertEqual(
            [p['option_code'] for p in without['CMD_OPEN']],
            ['CMD_OPEN_NONE'])
        with_scheme = resolve_slots(self.posi, signal_power=ext_pnp)
        self.assertEqual(
            [p['option_code'] for p in with_scheme['CMD_OPEN']],
            ['CMD_OPEN_NONE', 'CMD_OPEN_CONT'])
        self.assertEqual(
            [p['availability'] for p in with_scheme['CMD_OPEN']
             if p['option_code'] == 'CMD_OPEN_CONT'], ['opt'])

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
        self.assertEqual(len(mwg), 5)
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
                      if p['slot_code'] == 'TORQUE_SWITCHES_OPEN'
                      and p['option_code'] == 'TORQUE_OPEN_SPDT')
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


class CuUnitCopyDeleteTests(TestCase):
    """Actions copy/delete-unit у ControlUnitViewSet (связки матрицы/правил)."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        call_command('seed_cu_demo')
        cls.user = get_user_model().objects.create_superuser(
            'cu-tester', 't@example.com', 't')
        cls.basic = ControlUnit.objects.get(code='basic')

    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_copy_duplicates_matrix_rules_and_option(self):
        before_rows = CuMatrixEntry.objects.filter(
            control_unit=self.basic).count()
        r = self.client.post(
            f'/api/ea-control/control-units/{self.basic.id}/copy/')
        self.assertEqual(r.status_code, 201, r.content)
        new = ControlUnit.objects.get(pk=r.data['id'])
        self.assertIn('(копия)', new.name)
        self.assertEqual(
            CuMatrixEntry.objects.filter(control_unit=new).count(),
            before_rows)
        opt = CuSlotOption.objects.get(
            slot__code='control_unit', control_unit=new)
        # exact-правило (hide LOCAL_CONTROL) скопировано с новым кодом опции
        self.assertTrue(CuSlotRule.objects.filter(
            when_slot__code='control_unit', when_value=opt.code,
            target_slot__code='LOCAL_CONTROL').exists())
        # список 'in' расширен новым кодом опции
        in_rules = CuSlotRule.objects.filter(
            when_slot__code='control_unit',
            target_slot__code='CU_POWER_SUPPLY')
        self.assertTrue(any(opt.code in (rule.when_value or [])
                            for rule in in_rules))

    def test_delete_unit_cleans_option_rules_and_matrix(self):
        unit = ControlUnit.objects.get(code='int-o')
        opt = CuSlotOption.objects.get(
            slot__code='control_unit', control_unit=unit)
        r = self.client.delete(
            f'/api/ea-control/control-units/{unit.id}/delete-unit/')
        self.assertEqual(r.status_code, 204)
        self.assertFalse(ControlUnit.objects.filter(pk=unit.id).exists())
        self.assertFalse(CuSlotOption.objects.filter(pk=opt.pk).exists())
        self.assertFalse(CuMatrixEntry.objects.filter(
            control_unit=unit).exists())
        # код int-o убран из списков правил 'in'
        in_rules = CuSlotRule.objects.filter(
            when_slot__code='control_unit',
            target_slot__code='CU_POWER_SUPPLY')
        for rule in in_rules:
            self.assertNotIn(opt.code, rule.when_value or [])


class CuUnitMatrixServiceTests(TestCase):
    """Редактируемая матрица профиля БУ (вкладка «Настройки»)."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_cu_demo')
        from params.models import PowerSupplies
        cls.ps380 = PowerSupplies.objects.get(code='380-AC')
        cls.basic = ControlUnit.objects.get(code='basic')
        cls.int_unit = ControlUnit.objects.get(code='int-n')

    def test_build_matrix_basic(self):
        m = build_unit_matrix(self.basic)
        slots = {s['code']: s for s in m['slots']}
        self.assertIn('LOCAL_CONTROL', slots)
        opts = {o['code']: o for o in slots['LOCAL_CONTROL']['options']}
        self.assertEqual(opts['LOCAL_NONE']['availability'], 'std')
        self.assertEqual(opts['BUTTONS']['availability'], 'na')
        self.assertEqual(opts['SELECTOR']['availability'], 'na')

    def test_build_matrix_voltage_override(self):
        # на «любое напряжение» встроенного стартера нет (только на 380В)
        m_null = build_unit_matrix(self.int_unit)
        starter = next(s for s in m_null['slots']
                       if s['code'] == 'MOTOR_STARTER')
        sopts = {o['code']: o for o in starter['options']}
        self.assertEqual(sopts['STARTER_BUILT_IN']['availability'], 'na')
        self.assertEqual(sopts['STARTER_NONE']['availability'], 'opt')

        m_380 = build_unit_matrix(self.int_unit, power_supply=self.ps380)
        starter = next(s for s in m_380['slots']
                       if s['code'] == 'MOTOR_STARTER')
        sopts = {o['code']: o for o in starter['options']}
        self.assertEqual(sopts['STARTER_BUILT_IN']['availability'], 'std')
        self.assertFalse(sopts['STARTER_BUILT_IN']['inherited'])
        self.assertEqual(sopts['STARTER_NONE']['availability'], 'opt')
        self.assertTrue(sopts['STARTER_NONE']['inherited'])

    def test_apply_changes_upsert(self):
        # CMD_STOP: NONE уже std — повторный std обновляет ту же строку
        target = CuSlotOption.objects.get(code='CMD_STOP_NONE')
        slot = target.slot
        saved = apply_unit_matrix_changes(
            self.basic, None,
            [{'slot_id': slot.id, 'option_id': target.id,
              'availability': 'std'}])
        self.assertEqual(saved, 1)
        row = CuMatrixEntry.objects.get(
            slot=slot, option=target, control_unit=self.basic,
            power_supply__isnull=True, signal_power__isnull=True)
        self.assertEqual(row.availability, 'std')
        self.assertTrue(row.is_default)

    def test_apply_na_deletes_voltage_row(self):
        slot = CuSlot.objects.get(code='MOTOR_STARTER')
        built_in = CuSlotOption.objects.get(code='STARTER_BUILT_IN')
        self.assertTrue(CuMatrixEntry.objects.filter(
            slot=slot, option=built_in, control_unit=self.int_unit,
            power_supply=self.ps380).exists())
        saved = apply_unit_matrix_changes(
            self.int_unit, self.ps380,
            [{'slot_id': slot.id, 'option_id': built_in.id,
              'availability': 'na'}])
        self.assertEqual(saved, 1)
        self.assertFalse(CuMatrixEntry.objects.filter(
            slot=slot, option=built_in, control_unit=self.int_unit,
            power_supply=self.ps380).exists())

    def test_apply_rejects_multiple_std_in_single_slot(self):
        slot = CuSlot.objects.get(code='LOCAL_CONTROL')
        buttons = CuSlotOption.objects.get(code='BUTTONS')
        with self.assertRaises(MatrixValidationError):
            apply_unit_matrix_changes(
                self.basic, None,
                [{'slot_id': slot.id, 'option_id': buttons.id,
                  'availability': 'std'}])

    def test_apply_ignores_bare_rows_in_single_slot(self):
        # устаревшая bare-строка (option=None, «нет сигнала» старой
        # структуры) не считается std-опцией: пометка другой опции как
        # opt не должна давать ложную ошибку «две std»
        slot = CuSlot.objects.get(code='TORQUE_SWITCHES_OPEN')
        CuMatrixEntry.objects.create(
            slot=slot, option=None, control_unit=self.basic,
            availability='std')
        target = CuSlotOption.objects.get(code='TORQUE_OPEN_DPDT')
        saved = apply_unit_matrix_changes(
            self.basic, None,
            [{'slot_id': slot.id, 'option_id': target.id,
              'availability': 'opt'}])
        self.assertEqual(saved, 1)
        self.assertTrue(CuMatrixEntry.objects.filter(
            slot=slot, option=target, control_unit=self.basic,
            power_supply__isnull=True, signal_power__isnull=True,
            availability='opt').exists())
        # при этом два реальных std по-прежнему запрещены
        spdt = CuSlotOption.objects.get(code='TORQUE_OPEN_SPDT')
        with self.assertRaises(MatrixValidationError):
            apply_unit_matrix_changes(
                self.basic, None,
                [{'slot_id': slot.id, 'option_id': target.id,
                  'availability': 'std'}])
        self.assertEqual(CuMatrixEntry.objects.filter(
            slot=slot, option=spdt, control_unit=self.basic,
            availability='std').count(), 1)

    def test_apply_rule_changes(self):
        slot = CuSlot.objects.get(code='POSITION_FEEDBACK')
        saved = apply_unit_rule_changes(
            self.basic, [{'slot_id': slot.id, 'action': 'hide',
                          'action_value': None}])
        self.assertEqual(saved, 1)
        rule = CuSlotRule.objects.get(
            when_slot__code='control_unit', target_slot=slot,
            when_operator='exact', when_value='CU_BASIC')
        self.assertEqual(rule.action, 'hide')

        saved = apply_unit_rule_changes(
            self.basic, [{'slot_id': slot.id, 'action': 'require',
                          'action_value': None}])
        self.assertEqual(saved, 1)
        rule.refresh_from_db()
        self.assertEqual(rule.action, 'require')

        saved = apply_unit_rule_changes(
            self.basic, [{'slot_id': slot.id, 'action': None,
                          'action_value': None}])
        self.assertEqual(saved, 1)
        self.assertFalse(CuSlotRule.objects.filter(
            when_slot__code='control_unit', target_slot=slot,
            when_operator='exact', when_value='CU_BASIC').exists())

    def test_apply_rule_changes_in_list(self):
        slot = CuSlot.objects.get(code='WAY_SWITCHES_OPEN')
        saved = apply_unit_rule_changes(
            self.basic,
            [{'slot_id': slot.id, 'action': 'hide', 'action_value': None,
              'operator': 'in', 'when_value': ['CU_INT']}])
        self.assertEqual(saved, 1)
        rule = CuSlotRule.objects.get(
            when_slot__code='control_unit', target_slot=slot,
            when_operator='in')
        self.assertEqual(rule.action, 'hide')
        # текущий БУ (CU_BASIC) автоматически добавлен в список
        self.assertIn('CU_BASIC', rule.when_value)
        self.assertIn('CU_INT', rule.when_value)


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


class CuReviewFixTests(TestCase):
    """Регрессии по ревью 2026-10-26: полнота отчёта, имена опций схем,
    уникальность NULL-пар, валидация dry_input по внутреннему источнику."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_cu_demo')
        cls.basic = ControlUnit.objects.get(code='basic')

    def test_describe_keeps_child_of_deactivated_section(self):
        """M1: выключенный родитель не скрывает активных детей в отчёте."""
        from ea_control.models import CuSectionNode
        from ea_control.services.cu_report import build_description
        parent = CuSectionNode.objects.get(code='CONTROL_SIGNALS')
        prev = parent.is_active
        parent.is_active = False
        parent.save(update_fields=['is_active'])
        try:
            d = build_description(self.basic)
            codes = [s['code'] for s in d['sections']]
            self.assertIn('CMD_INPUTS', codes)
            sec = next(s for s in d['sections'] if s['code'] == 'CMD_INPUTS')
            self.assertIn('CMD_WIRING', [sl['code'] for sl in sec['slots']])
            # выключенная секция помечена в отчёте
            parent_sec = next(s for s in d['sections']
                              if s['code'] == 'CONTROL_SIGNALS')
            self.assertFalse(parent_sec['is_active'])
        finally:
            parent.is_active = prev
            parent.save(update_fields=['is_active'])

    def test_package_wiring_option_names_from_pairs(self):
        """M2: опции CMD_WIRING показывают имя пары, а не код опции."""
        pkg = build_package(self.basic, locale='ru')
        wiring = next(s for s in pkg['slots'] if s['code'] == 'CMD_WIRING')
        names = {o['code']: o['name'] for o in wiring['options']}
        self.assertEqual(names['W_EXT_220'], 'Внешний 220 В AC (потенциал)')
        self.assertEqual(names['W_INT_24'], 'Внутренний +24 В (сухой контакт)')

    def test_null_input_form_pair_unique(self):
        """L2: пары без формы входа уникальны (условный constraint)."""
        from django.db import IntegrityError, transaction
        from params.models import PowerSupplies
        from ea_control.models import CuSignalPower, CuSignalPowerSource
        source = CuSignalPowerSource.objects.get(code='EXTERNAL')
        ps = PowerSupplies.objects.first()
        CuSignalPower.objects.create(
            source=source, power_supply=ps, input_form=None,
            polarity='NOT_APPLICABLE', name='X')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CuSignalPower.objects.create(
                    source=source, power_supply=ps, input_form=None,
                    polarity='NOT_APPLICABLE', name='Y')

    def test_dry_input_requires_internal_source(self):
        """L3: сухой контакт (внутренний опрос) — только встроенный источник."""
        from django.core.exceptions import ValidationError
        from params.models import PowerSupplies
        from ea_control.models import (CuControlSignalForm, CuSignalPower,
                                       CuSignalPowerSource)
        ext = CuSignalPowerSource.objects.get(code='EXTERNAL')
        dry = CuControlSignalForm.objects.get(code='DRY_INPUT')
        pair = CuSignalPower(
            source=ext, power_supply=PowerSupplies.objects.first(),
            input_form=dry, polarity='NOT_APPLICABLE', name='X')
        with self.assertRaises(ValidationError):
            pair.full_clean()


class CuDictionaryCrudTests(TestCase):
    """Справочники с обязательными полями принимают полный PUT (регрессия 400)."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        call_command('seed_cu_demo')
        cls.user = get_user_model().objects.create_superuser(
            'cu-dict-tester', 'd@example.com', 't')

    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_control_signal_put_accepts_required_fields(self):
        sig = CuControlSignal.objects.get(code='CMD_4_20MA')
        form = CuControlSignalForm.objects.get(code='AN_4_20_PASSIVE')
        payload = {
            'code': sig.code, 'name': sig.name, 'role': sig.role,
            'category': sig.category, 'form': form.id,
            'hart': sig.hart, 'description': sig.description,
            'sorting_order': sig.sorting_order, 'is_active': sig.is_active,
        }
        r = self.client.put(
            f'/api/ea-control/control-signals/{sig.id}/', payload,
            format='json')
        self.assertEqual(r.status_code, 200, r.content)
