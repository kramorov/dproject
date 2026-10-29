# ea_control/tests.py
"""
Тесты фазы 2: конкретные паттерн-модели БУ.

Покрытие по плану (slots.md → «Проверка»): валидации kind-соответствия,
ограничения матрицы (один скоуп / одна полезная нагрузка), уникальность
кодов, std → is_default, локализованные имена, профильные строки,
evaluate правил, снимок.

Как запускать (тесты работают на **копии рабочей БД**, тестовая БД не
создаётся с нуля):

1. Обновить копию: скопировать ``db.sqlite3`` → ``test_db.sqlite3``
   (файл с именем тестовой БД из настроек TEST['NAME']).
2. ``python manage.py test ea_control --keepdb`` — существующая тестовая
   БД сохраняется, миграции применяются поверх (no-op для копии рабочей).

Если ``test_db.sqlite3`` удалить и запустить без ``--keepdb``, Django упадёт
на интерактивном вопросе о пересоздании тестовой БД (в скриптах используем
``interactive=False``).
"""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from ea_control.models import (CuCapability, CuCommProtocol, CuControlLogic,
                               CuControlSignal, CuFeedbackDevice,
                               CuFeedbackSignal, CuFeedbackSignalForm,
                               CuHeaterSupply, CuMatrixEntry, CuSignalPower,
                               CuSignalPowerSource, CuSlot, CuSlotOption,
                               CuSlotRule, ControlUnit, CuSectionNode,
                               AbstractConfigSnapshot)
from ea_control.models.abstract import ConfigAvailability
from ea_control.models.control_unit import ControlUnitKind


class CuConfigTestCase(TestCase):
    """Общая фабрика справочников для тестов матрицы и правил."""

    @classmethod
    def setUpTestData(cls):
        import unittest
        from params.models import PowerSupplies
        from producers.models import Brands

        # Тесты работают на копии рабочей БД — используем существующие записи
        # глобальных справочников (напряжения, бренды), а не создаём новые.
        cls.brand = Brands.objects.first()
        cls.power = PowerSupplies.objects.first()
        if cls.brand is None or cls.power is None:
            raise unittest.SkipTest('В рабочей БД нет Brands/PowerSupplies')
        # Идемпотентно: get_or_create, а не create — рабочая БД может быть уже
        # засеяна seed_cu_demo с теми же кодами (иначе при перекопировании
        # db.sqlite3 → test_db.sqlite3 падает IntegrityError).
        cls.form_dry = CuFeedbackSignalForm.objects.get_or_create(
            code='DRY_SPDT',
            defaults=dict(name='Сухой контакт SPDT', category='dry_output'))[0]
        cls.form_analog = CuFeedbackSignalForm.objects.get_or_create(
            code='AN_4_20_ACTIVE',
            defaults=dict(name='Петля 4-20 активная', category='current_4_20'))[0]
        cls.ctrl_signal = CuControlSignal.objects.get_or_create(
            code='CMD_OCS',
            defaults=dict(name='Команда О/С/З', role='CMD_OCS',
                          category='discrete'))[0]
        cls.fb_signal = CuFeedbackSignal.objects.get_or_create(
            code='FB_END_OPEN_SPDT',
            defaults=dict(name='Конечное «Открыто», SPDT', role='END_OPEN',
                          category='contact', form=cls.form_dry,
                          contact_normal='CHANGEOVER'))[0]
        cls.protocol = CuCommProtocol.objects.get_or_create(
            code='MODBUS_RTU',
            defaults=dict(name='Modbus RTU', transport='RS485'))[0]
        cls.device = CuFeedbackDevice.objects.get_or_create(
            code='POT_1K',
            defaults=dict(name='Потенциометр 1кОм', kind='POSITION_SENSOR',
                          technology='POTENTIOMETER'))[0]
        cls.device.emits.add(cls.fb_signal)
        cls.heater = CuHeaterSupply.objects.get_or_create(
            code='MOTOR_CIRCUIT',
            defaults=dict(name='От цепей питания'))[0]
        cls.cap = CuCapability.objects.get_or_create(
            code='ESD', defaults=dict(name='ESD'))[0]
        cls.source = CuSignalPowerSource.objects.get_or_create(
            code='EXTERNAL', defaults=dict(name='Внешний'))[0]
        cls.signal_power = CuSignalPower.objects.get_or_create(
            source=cls.source, power_supply=cls.power,
            input_form=None, polarity='NOT_APPLICABLE',
            defaults=dict(name='Внешний 220'))[0]
        cls.logic = CuControlLogic.objects.get_or_create(
            code='IMPULSE',
            defaults=dict(name='Импульсная', has_self_holding=True))[0]
        cls.cu = ControlUnit.objects.get_or_create(
            brand=cls.brand, code='INT',
            defaults=dict(name='Интеллектуальный БУ',
                          kind=ControlUnitKind.INTEGRATED))[0]
        cls.cu.accepts.add(cls.ctrl_signal)
        cls.cu.emits.add(cls.fb_signal)
        cls.cu.protocols.add(cls.protocol)
        cls.cu.capabilities.add(cls.cap)
        cls.section = CuSectionNode.objects.get_or_create(
            code='CONTROL_SIGNALS',
            defaults=dict(name='Сигналы управления'))[0]
        cls.slot_cmd = CuSlot.objects.get_or_create(
            code='CMD_OPEN',
            defaults=dict(name='Открыть', section=cls.section,
                          selection_mode='single'))[0]
        cls.slot_cu = CuSlot.objects.get_or_create(
            code='control_unit',
            defaults=dict(name='Тип БУ', slot_kind='object',
                          selection_mode='single'))[0]
        cls.slot_protocol = CuSlot.objects.get_or_create(
            code='PROTOCOL',
            defaults=dict(name='Шина', section=cls.section))[0]
        cls.slot_heater = CuSlot.objects.get_or_create(
            code='HEATER_CONTROL_UNIT',
            defaults=dict(name='Обогрев БУ'))[0]

    def make_option(self, **kwargs):
        return CuSlotOption.objects.create(**kwargs)


class CuSlotOptionTests(CuConfigTestCase):
    def test_signal_option_requires_exactly_one_payload(self):
        opt = self.make_option(
            code='X1', slot=self.slot_cmd, kind='signal',
            control_signal=self.ctrl_signal, feedback_signal=self.fb_signal)
        with self.assertRaises(ValidationError):
            opt.full_clean()

    def test_unit_option_only_for_control_unit_slot(self):
        opt = self.make_option(
            code='U1', slot=self.slot_cmd, kind='unit', control_unit=self.cu)
        with self.assertRaises(ValidationError):
            opt.full_clean()
        ok = self.make_option(
            code='U2', slot=self.slot_cu, kind='unit', control_unit=self.cu)
        ok.full_clean()  # не падает

    def test_none_option_requires_name(self):
        opt = self.make_option(code='N1', slot=self.slot_cmd, kind='none')
        with self.assertRaises(ValidationError):
            opt.full_clean()

    def test_option_encoding_defaults(self):
        """Справочные коды артикула у опции (переопределяются матрицей)."""
        opt = self.make_option(
            code='E1', slot=self.slot_cu, kind='unit', control_unit=self.cu,
            encoding='L', ext_encoding='E1')
        opt.full_clean()
        opt.save()
        opt.refresh_from_db()
        self.assertEqual(opt.encoding, 'L')
        self.assertEqual(opt.ext_encoding, 'E1')

    def test_option_code_unique(self):
        self.make_option(code='DUP', slot=self.slot_cmd, kind='none', name='Раз')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_option(code='DUP', slot=self.slot_cmd, kind='none',
                                 name='Два')


class CuMatrixEntryTests(CuConfigTestCase):
    def _row(self, **kwargs):
        base = dict(slot=self.slot_cmd, control_unit=self.cu,
                    power_supply=self.power, option=None)
        base.update(kwargs)
        return CuMatrixEntry(**base)

    def test_two_scopes_forbidden(self):
        row = self._row(brand=self.brand, model_line_id=1)
        with self.assertRaises(IntegrityError):
            row.save()

    def test_two_payloads_forbidden(self):
        row = self._row(control_signal=self.ctrl_signal,
                        feedback_signal=self.fb_signal)
        with self.assertRaises(IntegrityError):
            row.save()

    def test_profile_row_allowed(self):
        """Профильная строка: весь скоуп и контекст пусты — дефолт типа БУ."""
        row = self._row(control_unit=None, power_supply=None,
                        feedback_signal=self.fb_signal)
        row.full_clean()
        row.save()
        self.assertIsNone(row.brand)
        self.assertIsNone(row.model_line)
        self.assertIsNone(row.control_unit)

    def test_std_sets_default(self):
        row = self._row(control_signal=self.ctrl_signal,
                        availability=ConfigAvailability.STD)
        row.save()
        row.refresh_from_db()
        self.assertTrue(row.is_default)

    def test_localized_name_suffix(self):
        row = self._row(control_signal=self.ctrl_signal,
                        availability=ConfigAvailability.OPT)
        self.assertIn('(Опция)', row.localized_name())
        row.availability = ConfigAvailability.STD
        self.assertIn('(Стандарт)', row.localized_name())

    def test_protocol_only_in_protocol_slot(self):
        row = self._row(slot=self.slot_cmd, protocol=self.protocol)
        with self.assertRaises(ValidationError):
            row.full_clean()

    def test_device_must_emit_feedback_signal(self):
        other = CuFeedbackSignal.objects.create(
            code='FB_OTHER', name='Другой', role='ALARM', category='contact',
            form=self.form_dry)
        row = self._row(feedback_signal=other, device=self.device)
        with self.assertRaises(ValidationError):
            row.full_clean()

    def test_control_unit_slot_row_via_unit_option(self):
        """Строка слота control_unit: контекст пуст, опция — kind=unit."""
        opt = self.make_option(
            code='U3', slot=self.slot_cu, kind='unit', control_unit=self.cu)
        row = self._row(slot=self.slot_cu, option=opt,
                        control_unit=None, power_supply=None)
        row.full_clean()
        row.save()
        self.assertEqual(row.option.control_unit, self.cu)


class CuSlotRuleTests(CuConfigTestCase):
    def _rule(self, **kwargs):
        base = dict(when_slot=self.slot_cu, target_slot=self.slot_heater,
                    action='show')
        base.update(kwargs)
        return CuSlotRule(**base)

    def test_evaluate_exact(self):
        rule = self._rule(when_operator='exact', when_value='INT')
        self.assertTrue(rule.evaluate('INT'))
        self.assertFalse(rule.evaluate('BASIC'))

    def test_evaluate_in_and_gte(self):
        rule_in = self._rule(when_operator='in', when_value=['INT', 'POS'])
        self.assertTrue(rule_in.evaluate('POS'))
        rule_gte = self._rule(when_operator='gte', when_value=100)
        self.assertTrue(rule_gte.evaluate(100))
        self.assertFalse(rule_gte.evaluate(99))

    def test_evaluate_is_set(self):
        rule = self._rule(when_operator='is_set', when_value=None)
        self.assertTrue(rule.evaluate('INT'))
        self.assertFalse(rule.evaluate(None))


class ControlUnitTests(CuConfigTestCase):
    def test_creation_and_m2m(self):
        cu = ControlUnit.objects.get(code='INT')
        self.assertEqual(cu.kind, ControlUnitKind.INTEGRATED)
        self.assertIn(self.ctrl_signal, cu.accepts.all())
        self.assertIn(self.fb_signal, cu.emits.all())
        self.assertIn(self.protocol, cu.protocols.all())
        self.assertIn(self.cap, cu.capabilities.all())

    def test_brand_code_unique_together(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ControlUnit.objects.create(
                    brand=self.brand, code='INT', name='Дубль')

    def test_template_generation(self):
        """БУ сам себя описывает: имя/описание/спецификация из собственных
        шаблонов; save() автообновляет name/description из шаблонов."""
        cu = ControlUnit.objects.get(code='INT')
        cu.name_template = 'БУ {code} ({kind})'
        cu.description_template = 'Тип {name}; протоколы: {protocols}'
        cu.spec_template = {'Основные': {'Класс БУ': '_res_kind', 'Код': 'code'}}
        cu.name_template_i18n = {'en': 'CU {code} ({kind})'}
        cu.save()
        self.assertEqual(cu.name, 'БУ INT (Интеллектуальный)')
        self.assertEqual(cu.generate_name(), 'БУ INT (Интеллектуальный)')
        self.assertEqual(cu.generate_name(locale='en'),
                         'CU INT (Интеллектуальный)')
        self.assertEqual(
            cu.generate_description(),
            'Тип БУ INT (Интеллектуальный); протоколы: Modbus RTU')
        self.assertEqual(
            cu.generate_spec_sections(),
            {'Основные': {'Класс БУ': 'Интеллектуальный', 'Код': 'INT'}})


class SnapshotTests(TestCase):
    def test_apply_defaults_and_full_code(self):
        class TSnap(AbstractConfigSnapshot):
            class Meta:
                app_label = 'ea_control'

        s = TSnap()
        s.apply_defaults({'a': 1, 'b': 2})
        s.set_option('a', 9)
        self.assertEqual(s.config_snapshot, {'a': 9, 'b': 2})
        self.assertEqual(s.get_option('a'), 9)
        self.assertEqual(
            s.full_code([{'encoding': 'L', 'ext_encoding': 'E1'},
                         {}, {'encoding': 'M'}]), 'LME1')
