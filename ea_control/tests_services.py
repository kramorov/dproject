# ea_control/tests_services.py
"""
Тесты сервисов фазы 3 (Паттерн А и В) — на данных рабочей БД
(канон — БД, сид удалён; вариант C 2026-11-08).

Работают на копии рабочей БД (см. tests.py): сид выполняется в
setUpTestData; тесты не изменяют данные (только чтение резолверов).
"""
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
        from electric_actuators.models import ElectricActuatorModelLine
        from params.models import PowerSupplies
        cls.ar01e = ElectricActuatorModelLine.objects.get(code='AR01E')
        cls.ar11e = ElectricActuatorModelLine.objects.get(code='AR11E')
        cls.ps380 = PowerSupplies.objects.get(code='380-AC')
        cls.ps24 = PowerSupplies.objects.get(code='24-DC')
        cls.basic = ControlUnit.objects.get(code='basic AR21')
        cls.int_unit = ControlUnit.objects.get(code='INT/N')
        cls.posi = ControlUnit.objects.get(code='posi-4-20')

    def test_resolve_slots_basic(self):
        resolved = resolve_slots(self.basic)
        self.assertIn('LOCAL_CONTROL_DESIGN', resolved)
        # обогрев БУ у базового в каноне БД строк не имеет (удалён пользователем)
        self.assertNotIn('HEATER_CONTROL_UNIT', resolved)
        # базовому шину не резолвим — строк нет
        self.assertNotIn('PROTOCOL', resolved)
        # схема цепей: внешняя 220 В std; внутренний +24 В у базового
        # строк не имеет (канон БД — пользователь удалил)
        wiring = resolved['CMD_WIRING']
        self.assertTrue(any(p['option_code'] == 'W_EXT_220'
                            and p['availability'] == 'std' for p in wiring))
        self.assertFalse(any(p['option_code'] == 'W_INT_24'
                             for p in wiring))
        # стоп — отсутствием сигнала (опция «Отсутствие сигнала» std)
        stop = resolved['CMD_STOP']
        self.assertEqual([p['option_code'] for p in stop], ['CMD_STOP_NONE'])
        # AOX-M базовый: органов местного управления нет — только «Нет» (std)
        local = resolved['LOCAL_CONTROL_DESIGN']
        self.assertTrue(any(p['option_code'] == 'DESIGN_NONE'
                            and p['availability'] == 'std' for p in local))
        self.assertFalse(any(p['option_code'] == 'DESIGN_BTN' for p in local))
        self.assertFalse(any(p['option_code'] == 'DESIGN_SEL' for p in local))
        # обогрев привода — отдельной линией (std), от цепей питания — опция
        heater = resolved['ACTUATOR_HEATER']
        self.assertTrue(any(p['option_code'] == 'H_SEP_Copy'
                            and p['availability'] == 'std' for p in heater))
        self.assertTrue(any(p['option_code'] == 'H_MOTOR_Copy'
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
        self.assertIn('basic AR21', codes)
        self.assertIn('INT/N', codes)
        self.assertNotIn('posi-4-20', codes)  # na-запрет на 380
        default = [u for u in units if u['is_default']]
        self.assertEqual([u['code'] for u in default], ['basic AR21'])
        # option_code — код опции слота control_unit (для снимка/правил)
        self.assertEqual(default[0]['option_code'], 'CU_BASIC')

    def test_resolve_control_units_ar01e_24(self):
        units = resolve_control_units(self.ar01e, power_supply=self.ps24)
        codes = {u['code'] for u in units}
        self.assertIn('posi-4-20', codes)
        self.assertNotIn('basic AR21', codes)  # для 24В базовый не описан

    def test_resolve_control_units_ar11e(self):
        units = resolve_control_units(self.ar11e, power_supply=self.ps380)
        codes = {u['code'] for u in units}
        # у AR11E (Q) — INT (SRCU) и вариант LCU (местное управление)
        self.assertEqual(codes, {'INT/N', 'INT/L'})
        self.assertTrue(units[0]['is_default'])

    def test_profile_defaults_int(self):
        defaults = get_profile_defaults(self.int_unit)
        self.assertEqual(defaults.get('HEATER_CONTROL_UNIT'), 'H_NO')
        self.assertEqual(defaults.get('POSITION_FEEDBACK'), 'POS_4_20_ACTIVE')

    def test_bundle_atomicity(self):
        # пакет MWG — строки создаём в тесте (канон БД их не содержит;
        # вариант C: механика проверяется на локальных фикстурах)
        from ea_control.models import CuSlotOption
        opt = lambda code: CuSlotOption.objects.get(code=code)
        bundle_opts = [opt('POS_MWG'), opt('LIMIT_OPEN_NONE'),
                       opt('LIMIT_CLOSE_NONE'), opt('TORQUE_OPEN_NONE'),
                       opt('TORQUE_CLOSE_NONE')]
        for o in bundle_opts:
            CuMatrixEntry.objects.get_or_create(
                slot=o.slot, option=o, control_unit=self.int_unit,
                model_line=None, power_supply=None, signal_power=None,
                body=None, model_line_item=None, mode='both',
                defaults=dict(availability='opt', bundle='MWG'))
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
        # конфликт MWG × моментные SPDT — строки создаём в тесте (см. выше)
        from ea_control.models import CuSlotOption
        opt = lambda code: CuSlotOption.objects.get(code=code)
        bundle_opts = [opt('POS_MWG'), opt('LIMIT_OPEN_NONE'),
                       opt('LIMIT_CLOSE_NONE'), opt('TORQUE_OPEN_NONE'),
                       opt('TORQUE_CLOSE_NONE')]
        mwg_rows = []
        for o in bundle_opts:
            row, _ = CuMatrixEntry.objects.get_or_create(
                slot=o.slot, option=o, control_unit=self.int_unit,
                model_line=None, power_supply=None, signal_power=None,
                body=None, model_line_item=None, mode='both',
                defaults=dict(availability='opt', bundle='MWG'))
            mwg_rows.append(row)
        for key in (('TORQUE_SWITCHES_OPEN', 'TORQUE_OPEN_SPDT'),
                    ('TORQUE_SWITCHES_CLOSE', 'TORQUE_CLOSE_SPDT')):
            row = CuMatrixEntry.objects.get(
                slot__code=key[0], option__code=key[1],
                control_unit=self.int_unit)
            row.conflicts.add(mwg_rows[0])
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
        from ea_control.models import CuSlotRule
        cls.rules = CuSlotRule.objects.all()

    def test_basic_hides_protocol_and_setpoint(self):
        state = apply_rules(self.rules, {'control_unit': 'CU_BASIC'})
        self.assertFalse(state.get('PROTOCOL', {}).get('visible', True))
        self.assertFalse(state.get('SETPOINT', {}).get('visible', True))

    def test_int_protocol_visible_by_default(self):
        # шина без hide-правила — видна по умолчанию (скрыта только базовому)
        state = apply_rules(self.rules, {'control_unit': 'CU_INT'})
        self.assertTrue(state.get('PROTOCOL', {}).get('visible', True))

    def test_hart_set_default(self):
        state = apply_rules(self.rules, {'SETPOINT': 'SETPOINT_HART'})
        self.assertEqual(state['POSITION_FEEDBACK']['default'], 'POS_HART')

    def test_power_supply_controls_cu_cable_glands(self):
        # общий кабель — вводы БУ скрыты; отдельный кабель — показаны
        hidden = apply_rules(self.rules, {'CU_POWER_SUPPLY': 'PU_SHARED'})
        self.assertFalse(hidden.get('CU_CABLE_GLANDS', {})
                         .get('visible', True))
        shown = apply_rules(self.rules, {'CU_POWER_SUPPLY': 'PU_SEPARATE'})
        self.assertTrue(shown.get('CU_CABLE_GLANDS', {})
                        .get('visible', True))

    def test_int_o_keeps_cu_cable_glands_on_shared_power(self):
        # исключение: навесному БУ (CU_INT_O) вводы БУ видны всегда,
        # даже при общем кабеле питания (show с priority 1 перебивает hide)
        state = apply_rules(self.rules, {'control_unit': 'CU_INT_O',
                                         'CU_POWER_SUPPLY': 'PU_SHARED'})
        self.assertTrue(state.get('CU_CABLE_GLANDS', {})
                        .get('visible', True))


class CuUnitCopyDeleteTests(TestCase):
    """Actions copy/delete-unit у ControlUnitViewSet (связки матрицы/правил)."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        cls.user = get_user_model().objects.create_superuser(
            'cu-tester', 't@example.com', 't')
        cls.basic = ControlUnit.objects.get(code='basic AR21')

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
        # exact-правило (hide LOCAL_CONTROL_DESIGN) скопировано с новым кодом опции
        self.assertTrue(CuSlotRule.objects.filter(
            when_slot__code='control_unit', when_value=opt.code,
            target_slot__code='LOCAL_CONTROL_DESIGN').exists())
        # exact-правило hide CU_POWER_SUPPLY перезаписано на новый код опции
        self.assertTrue(CuSlotRule.objects.filter(
            when_slot__code='control_unit', when_value=opt.code,
            target_slot__code='CU_POWER_SUPPLY').exists())

    def test_delete_unit_cleans_option_rules_and_matrix(self):
        unit = ControlUnit.objects.get(code='INT/O')
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
        from params.models import PowerSupplies
        cls.ps380 = PowerSupplies.objects.get(code='380-AC')
        cls.basic = ControlUnit.objects.get(code='basic AR21')
        cls.int_unit = ControlUnit.objects.get(code='INT/N')
        cls.int_o = ControlUnit.objects.get(code='INT/O')

    def test_build_matrix_basic(self):
        m = build_unit_matrix(self.basic)
        slots = {s['code']: s for s in m['slots']}
        self.assertIn('LOCAL_CONTROL_DESIGN', slots)
        opts = {o['code']: o for o in slots['LOCAL_CONTROL_DESIGN']['options']}
        self.assertEqual(opts['DESIGN_NONE']['availability'], 'std')
        self.assertEqual(opts['DESIGN_BTN']['availability'], 'na')
        self.assertEqual(opts['DESIGN_SEL']['availability'], 'na')

    def test_build_matrix_location_slot(self):
        # размещение БУ — слот CU_LOCATION: встроенному basic — BUILT_IN std,
        # навесному INT/O — MOUNTED std (отдельное размещение — opt)
        m = build_unit_matrix(self.basic)
        loc = next(s for s in m['slots'] if s['code'] == 'CU_LOCATION')
        opts = {o['code']: o for o in loc['options']}
        self.assertEqual(opts['BUILT_IN']['availability'], 'std')
        self.assertEqual(opts['CU_LOC_SEPARATE']['availability'], 'na')

        m2 = build_unit_matrix(self.int_o)
        loc2 = next(s for s in m2['slots'] if s['code'] == 'CU_LOCATION')
        opts2 = {o['code']: o for o in loc2['options']}
        self.assertEqual(opts2['CU_LOC_MOUNTED']['availability'], 'std')
        self.assertEqual(opts2['CU_LOC_SEPARATE']['availability'], 'opt')

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
        slot = CuSlot.objects.get(code='LOCAL_CONTROL_DESIGN')
        buttons = CuSlotOption.objects.get(code='DESIGN_BTN')
        with self.assertRaises(MatrixValidationError):
            apply_unit_matrix_changes(
                self.basic, None,
                [{'slot_id': slot.id, 'option_id': buttons.id,
                  'availability': 'std'}])

    def test_multi_slot_allows_multiple_std(self):
        # multi — осознанное исключение: несколько предвыборов допустимы
        slot = CuSlot.objects.create(
            code='TMP_MULTI', name='x', selection_mode='multi')
        a = CuSlotOption.objects.create(
            slot=slot, code='TMP_MULTI_A', kind='none', name='A')
        b = CuSlotOption.objects.create(
            slot=slot, code='TMP_MULTI_B', kind='none', name='B')
        saved = apply_unit_matrix_changes(
            self.basic, None,
            [{'slot_id': slot.id, 'option_id': a.id,
              'availability': 'std'},
             {'slot_id': slot.id, 'option_id': b.id,
              'availability': 'std'}])
        self.assertEqual(saved, 2)
        self.assertEqual(CuMatrixEntry.objects.filter(
            slot=slot, availability='std').count(), 2)

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
        from electric_actuators.models import ElectricActuatorModelLine
        from params.models import PowerSupplies
        cls.ar01e = ElectricActuatorModelLine.objects.get(code='AR01E')
        cls.ps380 = PowerSupplies.objects.get(code='380-AC')

    def test_build_package(self):
        unit = ControlUnit.objects.get(code='INT/N')
        pkg = build_package(unit, model_line=self.ar01e, power_supply=self.ps380,
                            locale='ru')
        self.assertEqual(pkg['unit']['code'], 'INT/N')
        self.assertTrue(pkg['unit']['name'])
        self.assertTrue(pkg['sections'])
        self.assertTrue(pkg['slots'])
        # протоколы INT/N: без протокола — std, HART/ModBus/ProfiBus/ProfiNet — opt
        protocol = next(s for s in pkg['slots'] if s['code'] == 'PROTOCOL')
        av = {o['code']: o['availability'] for o in protocol['options']}
        self.assertEqual(av.get('DP_NONE'), 'std')
        for code in ('HART', 'MB_RTU', 'PB_DP', 'PN'):
            self.assertEqual(av.get(code), 'opt', code)
        # опции POSITION_FEEDBACK: POS_4_20_ACTIVE доступна как std
        pos_fb = next(s for s in pkg['slots'] if s['code'] == 'POSITION_FEEDBACK')
        active = next(o for o in pos_fb['options']
                      if o['code'] == 'POS_4_20_ACTIVE')
        self.assertEqual(active['availability'], 'std')
        self.assertEqual(pkg['defaults'].get('POSITION_FEEDBACK'),
                         'POS_4_20_ACTIVE')
        self.assertTrue(pkg['rules'])


class CuReviewFixTests(TestCase):
    """Регрессии по ревью 2026-10-26: полнота отчёта, имена опций схем,
    уникальность NULL-пар, валидация dry_input по внутреннему источнику."""

    @classmethod
    def setUpTestData(cls):
        cls.basic = ControlUnit.objects.get(code='basic AR21')

    def test_describe_keeps_child_of_deactivated_section(self):
        """M1: выключенный родитель не скрывает активных детей в отчёте."""
        from ea_control.models import ControlUnit, CuSectionNode
        from ea_control.services.cu_report import build_description
        unit = ControlUnit.objects.get(code='INT/N')
        parent = CuSectionNode.objects.get(code='GENERAL')
        prev = parent.is_active
        parent.is_active = False
        parent.save(update_fields=['is_active'])
        try:
            d = build_description(unit)
            codes = [s['code'] for s in d['sections']]
            # ребёнок выключенной секции виден (PHASE_3_OPTIONS →
            # PHASE_PROTECTION — видим для int-n)
            self.assertIn('PHASE_3_OPTIONS', codes)
            child = next(s for s in d['sections']
                         if s['code'] == 'PHASE_3_OPTIONS')
            self.assertIn('PHASE_PROTECTION',
                          [sl['code'] for sl in child['slots']])
            # выключенная секция помечена в отчёте (если у неё есть
            # видимые слоты)
            parent_sec = next(s for s in d['sections']
                              if s['code'] == 'GENERAL')
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
        from ea_control.models import (CuPolarity, CuSignalPower,
                                       CuSignalPowerSource)
        source = CuSignalPowerSource.objects.get(code='EXTERNAL')
        ps = PowerSupplies.objects.first()
        polarity = CuPolarity.objects.get(code='NOT_APPLICABLE')
        CuSignalPower.objects.create(
            source=source, power_supply=ps, input_form=None,
            polarity=polarity, name='X')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CuSignalPower.objects.create(
                    source=source, power_supply=ps, input_form=None,
                    polarity=polarity, name='Y')

    def test_dry_input_requires_internal_source(self):
        """L3: сухой контакт (внутренний опрос) — только встроенный источник."""
        from django.core.exceptions import ValidationError
        from params.models import PowerSupplies
        from ea_control.models import (CuControlSignalForm, CuPolarity,
                                       CuSignalPower, CuSignalPowerSource)
        ext = CuSignalPowerSource.objects.get(code='EXTERNAL')
        dry = CuControlSignalForm.objects.get(code='DRY_24VDC')
        pair = CuSignalPower(
            source=ext, power_supply=PowerSupplies.objects.first(),
            input_form=dry, polarity=CuPolarity.objects.get(code='NOT_APPLICABLE'),
            name='X')
        with self.assertRaises(ValidationError):
            pair.full_clean()


    def test_analog_0_10v_forms_valid(self):
        """0-10 В — валидная аналоговая форма уставки и ОС."""
        from ea_control.models.dictionaries import (
            CuControlSignalForm, CuControlSignal, CuFeedbackSignalForm,
            CuFeedbackSignal)
        ctl_form = CuControlSignalForm.objects.get(code='AN_0_10V_ACTIVE')
        fb_form = CuFeedbackSignalForm.objects.get(code='AN_0_10V_PASSIVE')
        sig = CuControlSignal(
            code='CMD_TEST_0_10V', name='X',
            role=CuControlSignal.objects.get(
                code='CMD_POS_0_10V_ACTIVE').role,
            category='analog', form=ctl_form, wires=2)
        sig.full_clean()
        fb = CuFeedbackSignal(
            code='FB_TEST_0_10V', name='X',
            role=CuFeedbackSignal.objects.get(code='FB_POS_0_10V').role,
            category='analog', form=fb_form, wires=2)
        fb.full_clean()

    def test_hart_rejected_on_0_10v_form(self):
        """HART — только на токовой петле 4-20 мА (не 0-10 В)."""
        from django.core.exceptions import ValidationError
        from ea_control.models.dictionaries import (
            CuControlSignalForm, CuControlSignal)
        form = CuControlSignalForm.objects.get(code='AN_0_10V_ACTIVE')
        sig = CuControlSignal(
            code='CMD_TEST_HART_0_10', name='X',
            role=CuControlSignal.objects.get(
                code='CMD_POS_0_10V_ACTIVE').role,
            category='analog', form=form, hart=True, wires=2)
        with self.assertRaises(ValidationError):
            sig.full_clean()


class CuDictionaryCrudTests(TestCase):
    """Справочники с обязательными полями принимают полный PUT (регрессия 400)."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        cls.user = get_user_model().objects.create_superuser(
            'cu-dict-tester', 'd@example.com', 't')

    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_control_signal_put_accepts_required_fields(self):
        sig = CuControlSignal.objects.get(code='CMD_4_20MA_P')
        form = CuControlSignalForm.objects.get(code='AN_4_20_PASSIVE')
        payload = {
            'code': sig.code, 'name': sig.name, 'role': sig.role_id,
            'category': sig.category, 'form': form.id,
            'hart': sig.hart, 'description': sig.description,
            'sorting_order': sig.sorting_order, 'is_active': sig.is_active,
        }
        r = self.client.put(
            f'/api/ea-control/control-signals/{sig.id}/', payload,
            format='json')
        self.assertEqual(r.status_code, 200, r.content)

class CuDbCanonTests(TestCase):
    """Канон БД (вариант C: единственный источник правды — БД).

    Проверяет текущее состояние рабочей БД (тесты гоняются на её копии).
    """

    def test_db_canonical_state(self):
        self.assertEqual(CuSlot.objects.count(), 45)
        # единственный не-single — PHASE_PROTECTION (xor, слот пользователя)
        self.assertEqual(
            CuSlot.objects.exclude(selection_mode='single').count(), 1)
        self.assertEqual(
            CuSlot.objects.get(code='PHASE_PROTECTION').selection_mode, 'xor')
        # 41 object-слот с источником, 4 value-слота
        self.assertEqual(CuSlot.objects.filter(slot_kind='object').count(), 41)
        self.assertEqual(
            CuSlot.objects.filter(slot_kind='object', source='').count(), 0)
        self.assertEqual(CuSlot.objects.filter(slot_kind='value').count(), 4)
        self.assertEqual(
            CuSlot.objects.get(code='POSITION_FEEDBACK').source,
            'feedback_signal')
        self.assertEqual(
            CuSlot.objects.get(code='LOCAL_CONTROL_DESIGN').source,
            'local_control')
        self.assertEqual(
            CuSlot.objects.get(code='ACCESS_DEVICE').source, 'access_device')
        # слоты LOCAL_CONTROL/INDICATOR заменены (решение 2026-11-02):
        # обогрев привода (object/heater_supply) и защита фаз (value/xor)
        self.assertFalse(CuSlot.objects.filter(
            code__in=('LOCAL_CONTROL', 'INDICATOR', 'IND_POSITION')).exists())
        # слоты пользователя (канон БД 2026-11-08): индикаторы положения,
        # потенциометр, теплоизоляционный кожух
        self.assertEqual(
            CuSlot.objects.get(code='IND_POSITION_LCD').source, 'display')
        self.assertEqual(
            CuSlot.objects.get(code='IND_POSITION_MECH').source, 'display')
        self.assertEqual(CuSlot.objects.get(code='POTE').source, 'device')
        self.assertEqual(
            CuSlot.objects.get(code='POTE').section.code, 'SENSOR')
        self.assertEqual(
            CuSlot.objects.get(code='THERMAL_PROTECTION_COAT').slot_kind,
            'value')
        # питание БУ — слот выключен (канон БД)
        self.assertFalse(
            CuSlot.objects.get(code='CU_POWER_SUPPLY').is_active)
        self.assertEqual(
            CuSlot.objects.get(code='ACTUATOR_HEATER').source,
            'heater_supply')
        self.assertEqual(
            CuSlot.objects.get(code='PHASE_PROTECTION').slot_kind, 'value')
        self.assertEqual(
            CuSlot.objects.get(code='PHASE_PROTECTION').selection_mode, 'xor')
        # узел «Датчики» — тип датчика (device), не сигнал: концевые/путевые/
        # моментные × основные/дополнительные + теплозащита
        for code in ('END_SWITCHES_SENSOR_MAIN', 'END_SWITCHES_SENSOR_EXT',
                     'WAY_SWITCHES_SENSOR_MAIN', 'WAY_SWITCHES_SENSOR_EXT',
                     'TORQUE_SWITCHES_SENSOR_MAIN',
                     'TORQUE_SWITCHES_SENSOR_EXT', 'THERMO_SENSOR'):
            slot = CuSlot.objects.get(code=code)
            self.assertEqual(slot.source, 'device')
            self.assertEqual(slot.section.code, 'SENSOR')
        self.assertEqual(CuSlot.objects.get(code='TURN_COUNTER').source, '')
        self.assertEqual(ControlUnit.objects.count(), 5)
        self.assertEqual(
            set(ControlUnit.objects.values_list('code', flat=True)),
            {'basic AR21', 'INT/N', 'INT/L', 'INT/O', 'posi-4-20'})
        self.assertFalse(ControlUnit.objects.filter(
            code__in=('basic', 'int-n', 'int-n-mb', 'int-n-hr', 'int-n-pb',
                      'int-l', 'int-o')).exists())

    def test_seed_dictionary_canon(self):
        """Справочники — канон: 0-10В, протоколы, энкодеры АУМА, размещение."""
        from ea_control.models.dictionaries import (
            CuControlSignalForm, CuFeedbackSignalForm, CuControlSignal,
            CuFeedbackSignal, CuCommProtocol, CuFeedbackDevice,
            CuLocationOption)
        for code in ('AN_0_10V_ACTIVE', 'AN_0_10V_PASSIVE'):
            self.assertTrue(
                CuControlSignalForm.objects.filter(code=code).exists())
            self.assertTrue(
                CuFeedbackSignalForm.objects.filter(code=code).exists())
        for code in ('CMD_POS_0_10V_ACTIVE', 'CMD_POS_0_10V_PASSIVE'):
            self.assertTrue(CuControlSignal.objects.filter(code=code).exists())
        self.assertTrue(
            CuFeedbackSignal.objects.filter(code='FB_POS_0_10V').exists())
        for code in ('MODBUS_TCP', 'ETHERNET_IP', 'DEVICENET',
                     'FOUNDATION_FIELDBUS', 'PAKSCAN'):
            self.assertTrue(CuCommProtocol.objects.filter(code=code).exists())
        for code in ('EWG_01_1', 'RWG_4020'):
            self.assertTrue(CuFeedbackDevice.objects.filter(code=code).exists())
        self.assertEqual(
            set(CuLocationOption.objects.values_list('code', flat=True)),
            {'BUILT_IN', 'MOUNTED', 'SEPARATE'})
        self.assertFalse(
            CuControlSignalForm.objects.filter(code='TMP_FORM5').exists())
        self.assertFalse(
            CuControlSignal.objects.filter(code='CMD_4_20MA').exists())
        # HART-ОС активная — на активной петле (фикс 2026-11-08)
        hart = CuFeedbackSignal.objects.get(code='FB_POS_4_20MA_ACTIVE_HART')
        self.assertEqual(hart.form.code, 'AN_4_20_ACTIVE')
