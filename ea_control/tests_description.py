# ea_control/tests_description.py
"""
Тесты генератора описания/спецификации/артикула модификации БУ
(cu_description) — решение 2026-11-02: видимость «всё, кроме hide»,
артикул из кодов узла/слота/опции, локализация через *_i18n, без хранения.

Сценарии рассинхрона (модель без хранения):
- снимок с устаревшими/чужими кодами опций не ломает генерацию;
- изменение состава опций конкретного БУ (строки матрицы) сразу видно
  в спецификации;
- изменение правил (hide) сразу убирает слот из описания/спецификации.
"""
from django.core.management import call_command
from django.test import TestCase

from ea_control.models import (CuMatrixEntry, CuSectionNode, CuSlot,
                               CuSlotOption)
from ea_control.services.cu_description import (assemble_article,
                                                build_description,
                                                build_specification,
                                                hidden_slot_codes,
                                                _option_description,
                                                _option_text)


class CuDescriptionGeneratorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_cu_demo')
        from ea_control.models import ControlUnit
        cls.basic = ControlUnit.objects.get(code='basic')
        cls.int_unit = ControlUnit.objects.get(code='int-n')
        cls.int_o = ControlUnit.objects.get(code='int-o')
        cls.posi = ControlUnit.objects.get(code='posi-4-20')

    # ── видимость: «всё, кроме hide» ────────────────────────────────────

    def test_hidden_slots_by_rules(self):
        hidden = hidden_slot_codes(self.basic)
        # exact-hide для базового
        for code in ('LOCAL_CONTROL_DESIGN', 'IND_STOP', 'IND_LOCAL_REMOTE',
                     'IND_POSITION', 'IND_ALARM', 'MOTOR_STARTER',
                     'PHASE_PROTECTION'):
            self.assertIn(code, hidden)
        # in-hide для встроенных БУ без шины
        self.assertIn('CU_POWER_SUPPLY', hidden)
        self.assertIn('CU_CABLE_GLANDS', hidden)
        self.assertIn('PROTOCOL', hidden)
        # видимые остаются
        for code in ('CU_LOCATION', 'CMD_WIRING', 'ACTUATOR_HEATER',
                     'HEATER_CONTROL_UNIT', 'IND_OPEN'):
            self.assertNotIn(code, hidden)

    def test_spec_contains_only_visible_slots(self):
        spec = build_specification(self.basic)
        all_slots = {s['code'] for sec in spec['sections'] for s in sec['slots']}
        self.assertIn('CMD_WIRING', all_slots)
        self.assertIn('ACTUATOR_HEATER', all_slots)
        self.assertNotIn('MOTOR_STARTER', all_slots)
        self.assertNotIn('CU_POWER_SUPPLY', all_slots)
        self.assertNotIn('CU_CABLE_GLANDS', all_slots)
        self.assertNotIn('PHASE_PROTECTION', all_slots)

    def test_node_without_visible_slots_dropped(self):
        spec = build_specification(self.basic)
        codes = [sec['code'] for sec in spec['sections']]
        # узлы только с видимыми слотами; пустых нет
        for sec in spec['sections']:
            self.assertTrue(sec['slots'])
        # местная индикация: только видимые сигналы (СТОП/Авария скрыты)
        ind_signals = next(sec for sec in spec['sections']
                           if sec['code'] == 'IND_SIGNALS')
        self.assertEqual({s['code'] for s in ind_signals['slots']},
                         {'IND_OPEN', 'IND_CLOSED', 'IND_RUN'})
        # узел LOCAL_INDICATION — только ACCESS_DEVICE
        loc_ind = next(sec for sec in spec['sections']
                       if sec['code'] == 'LOCAL_INDICATION')
        self.assertEqual({s['code'] for s in loc_ind['slots']},
                         {'ACCESS_DEVICE'})

    # ── значения: снимок, дефолты, рассинхрон ───────────────────────────

    def test_spec_values_from_profile_std(self):
        spec = build_specification(self.basic)
        values = {s['code']: s['value']
                  for sec in spec['sections'] for s in sec['slots']}
        self.assertEqual(values['CMD_WIRING'], 'Внешний 220 В AC (потенциал)')
        self.assertEqual(values['ACTUATOR_HEATER'], 'Отдельная линия')

    def test_snapshot_overrides_std(self):
        spec = build_specification(
            self.basic, snapshot={'CMD_WIRING': 'W_INT_24'})
        values = {s['code']: s['value']
                  for sec in spec['sections'] for s in sec['slots']}
        self.assertEqual(values['CMD_WIRING'],
                         'Внутренний +24 В (сухой контакт)')

    def test_value_description_none_option(self):
        """Колонка «Описание»: у none-опции — явное «Нет», не пусто."""
        spec = build_specification(self.basic)
        slots = {s['code']: s
                 for sec in spec['sections'] for s in sec['slots']}
        self.assertEqual(slots['IND_OPEN']['value'], 'Нет')
        self.assertEqual(slots['IND_OPEN']['value_description'], 'Нет')

    def test_value_description_from_payload_record(self):
        """Колонка «Описание» объектной опции — описание справочной
        записи (локализованное)."""
        heater = CuSlotOption.objects.get(code='H_SEP_Copy').heater_supply
        heater.description_i18n = {'en': 'Separate heater line'}
        heater.save()
        try:
            spec = build_specification(self.basic, locale='en')
            slots = {s['code']: s
                     for sec in spec['sections'] for s in sec['slots']}
            self.assertEqual(slots['ACTUATOR_HEATER']['value_description'],
                             'Separate heater line')
        finally:
            heater.description_i18n = {}
            heater.save()

    def test_value_description_snapshot_override(self):
        """Смена выбранной опции снимком меняет и описание выбранной."""
        spec = build_specification(
            self.basic, snapshot={'CMD_WIRING': 'W_INT_24'})
        wiring = next(s for sec in spec['sections'] for s in sec['slots']
                      if s['code'] == 'CMD_WIRING')
        self.assertEqual(wiring['value'],
                         'Внутренний +24 В (сухой контакт)')
        # описание — у записи схемы (CuSignalPower.description), может
        # быть пустым; главное — поле присутствует и не «Нет»/не None
        self.assertIn('value_description', wiring)
        self.assertNotEqual(wiring['value_description'], 'Нет')

    def test_none_option_description_explicit(self):
        """_option_description none-опции — имя («Нет»), а не пусто/код."""
        opt = CuSlotOption.objects.get(code='POS_NONE')
        self.assertEqual(opt.kind, 'none')
        self.assertEqual(_option_description(opt), 'Нет')

    def test_stale_snapshot_codes_ignored(self):
        """Рассинхрон снимка с составом БУ: чужие коды — без ошибок,
        значение падает на профильный std."""
        snapshot = {'CMD_WIRING': 'GONE_OPTION', 'GHOST_SLOT': 'X',
                    'CU_LOCATION': 'CU_LOC_SEPARATE'}  # na для базового
        spec = build_specification(self.basic, snapshot=snapshot)
        values = {s['code']: s['value']
                  for sec in spec['sections'] for s in sec['slots']}
        self.assertEqual(values['CMD_WIRING'], 'Внешний 220 В AC (потенциал)')

    def test_option_set_change_reflected(self):
        """Убрали строки матрицы у слота — спецификация видит это сразу."""
        slot = CuSlot.objects.get(code='CMD_STOP')
        CuMatrixEntry.objects.filter(slot=slot,
                                     control_unit=self.basic).delete()
        spec = build_specification(self.basic)
        stop = next(s for sec in spec['sections'] for s in sec['slots']
                    if s['code'] == 'CMD_STOP')
        self.assertIsNone(stop['value'])
        self.assertTrue(all(o['availability'] == 'na'
                            for o in stop['options']))

    def test_hide_rule_change_reflected(self):
        """Добавили hide-правило — слот исчез из спецификации."""
        from ea_control.models import CuSlotRule
        rule = CuSlotRule.objects.create(
            when_slot=CuSlot.objects.get(code='control_unit'),
            target_slot=CuSlot.objects.get(code='IND_OPEN'),
            action='hide', when_value='CU_BASIC',
            description='test-hide-IND_OPEN')
        try:
            spec = build_specification(self.basic)
            all_slots = {s['code'] for sec in spec['sections']
                         for s in sec['slots']}
            self.assertNotIn('IND_OPEN', all_slots)
        finally:
            rule.delete()

    def test_inactive_node_keeps_visible_slots(self):
        """Выключенный узел с активными видимыми слотами: спецификация не
        теряет слоты (узел помечен is_active=False), артикул не падает."""
        node = CuSlot.objects.get(code='ACTUATOR_HEATER').section
        prev = node.is_active
        node.is_active = False
        node.save(update_fields=['is_active'])
        try:
            spec = build_specification(self.basic)
            sec = next(s for s in spec['sections'] if s['code'] == node.code)
            self.assertFalse(sec['is_active'])
            self.assertIn('ACTUATOR_HEATER',
                          [s['code'] for s in sec['slots']])
            article = assemble_article(self.basic)
            self.assertIn(f'{node.code}.ACTUATOR_HEATER', article)
        finally:
            node.is_active = prev
            node.save(update_fields=['is_active'])

    def test_spec_accepts_signal_power_parameter(self):
        """Параметр signal_power прокидывается в резолвер (координата схемы
        цепей) и не ломает спецификацию. Сам пересчёт набора сигналов по
        координате покрыт тестом резолвера
        (tests_services.test_signal_power_coordinate_posi); в спецификации
        слоты CMD_* у позиционера скрыты правилом hide, поэтому здесь —
        только smoke-проверка."""
        from ea_control.models import CuSignalPower
        ext_pnp = CuSignalPower.objects.get(
            name__startswith='Внешний 24 В DC (PNP)')
        spec = build_specification(self.posi, signal_power=ext_pnp)
        slots = {s['code'] for sec in spec['sections']
                 for s in sec['slots']}
        self.assertIn('POSITION_FEEDBACK', slots)
        self.assertIn('SETPOINT', slots)
        self.assertNotIn('CMD_OPEN', slots)  # hide-правило позиционера

    # ── артикул из кодов ────────────────────────────────────────────────

    def test_article_from_codes(self):
        article = assemble_article(self.basic)
        parts = article.split('/')
        self.assertEqual(parts[0], 'CU_BASIC')
        self.assertIn('GENERAL.ACTUATOR_HEATER.H_SEP_Copy', parts)
        self.assertIn('CMD_INPUTS.CMD_WIRING.W_EXT_220', parts)
        self.assertIn('CMD_INPUTS.CMD_STOP.CMD_STOP_NONE', parts)
        heater_sec = CuSlot.objects.get(
            code='HEATER_CONTROL_UNIT').section.code
        self.assertIn(f'{heater_sec}.HEATER_CONTROL_UNIT.H_SEP', parts)
        # каждый вклад — ровно один на слот: «узел.слот.опция»
        self.assertTrue(all(p.count('.') == 2 for p in parts[1:]))
        # скрытые слоты в артикул не входят
        self.assertFalse(any('MOTOR_STARTER' in p for p in parts))
        self.assertFalse(any('CU_POWER_SUPPLY' in p for p in parts))
        self.assertFalse(any('CU_CABLE_GLANDS' in p for p in parts))

    def test_article_uses_snapshot_choice(self):
        article = assemble_article(
            self.basic, snapshot={'CMD_WIRING': 'W_INT_24'})
        self.assertIn('CMD_INPUTS.CMD_WIRING.W_INT_24', article.split('/'))
        self.assertNotIn('CMD_INPUTS.CMD_WIRING.W_EXT_220', article.split('/'))

    def test_article_stale_code_falls_back_to_std(self):
        article = assemble_article(
            self.basic, snapshot={'CMD_WIRING': 'GONE_OPTION'})
        self.assertIn('CMD_INPUTS.CMD_WIRING.W_EXT_220', article.split('/'))

    # ── локализация ─────────────────────────────────────────────────────

    def test_slot_and_node_description_i18n(self):
        slot = CuSlot.objects.get(code='CMD_WIRING')
        slot.description_i18n = {'en': 'Control wiring', 'cn': '控制接线'}
        slot.save()
        node = CuSectionNode.objects.get(code='GENERAL')
        node.description_i18n = {'en': 'General parameters'}
        node.save()
        try:
            spec_en = build_specification(self.basic, locale='en')
            wiring = next(s for sec in spec_en['sections']
                          for s in sec['slots'] if s['code'] == 'CMD_WIRING')
            self.assertEqual(wiring['description'], 'Control wiring')
            general = next(sec for sec in spec_en['sections']
                           if sec['code'] == 'GENERAL')
            self.assertEqual(general['description'], 'General parameters')
            # нет перевода cn — fallback на ru-описание (или пусто)
            spec_cn = build_specification(self.basic, locale='cn')
            wiring_cn = next(s for sec in spec_cn['sections']
                             for s in sec['slots']
                             if s['code'] == 'CMD_WIRING')
            self.assertEqual(wiring_cn['description'], '控制接线')
        finally:
            slot.description_i18n = {}
            slot.save()
            node.description_i18n = {}
            node.save()

    def test_value_option_description_i18n(self):
        """Текстовое значение опции берётся из description_i18n по локали."""
        opt = CuSlotOption.objects.get(code='PHASE_PROTECTION_YES')
        opt.description_i18n = {'en': 'YES', 'cn': '有'}
        opt.save()
        try:
            self.assertEqual(_option_text(opt, 'en'), 'YES')
            self.assertEqual(_option_text(opt, 'cn'), '有')
            self.assertEqual(_option_text(opt, 'ru'), 'ЕСТЬ')
        finally:
            opt.description_i18n = {}
            opt.save()

    def test_description_text_localized(self):
        slot = CuSlot.objects.get(code='CU_LOCATION')
        slot.name_i18n = {'en': 'Mounting'}
        slot.save()
        try:
            text = build_description(self.basic, locale='en')
            self.assertIn('Mounting', text)
            text_ru = build_description(self.basic, locale='ru')
            self.assertIn('Размещение БУ', text_ru)
        finally:
            slot.name_i18n = {}
            slot.save()
