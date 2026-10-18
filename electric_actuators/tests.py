# electric_actuators/tests.py
"""
Тесты справочников сигналов ЭП (фаза 2 плана переезда).

Покрывают: валидации «категория × форма», HART на не-аналоговой форме,
потенциометр без сопротивления, contact_normal только для контактов,
синхронизацию ru в *_i18n, get_for_select с локалью, копирование через
CopyMixin (уникальный code с суффиксом).
"""
from django.core.exceptions import ValidationError
from django.test import TestCase

from electric_actuators.models import (
    EaSignalForm, EaControlSignal, EaFeedbackSignal, EaCommProtocol,
    EaSignalMatrixEntry, EaWiringDiagramBinding, EaSignalSlot,
)
from params.models import ControlUnitInstalledOption


class EaSignalFormTests(TestCase):
    def test_create_form_and_i18n_sync(self):
        form = EaSignalForm.objects.create(
            code='DRY_SPDT', name='Сухой контакт SPDT', category='contact')
        self.assertEqual(form.name_i18n.get('ru'), 'Сухой контакт SPDT')
        self.assertEqual(form.description_i18n.get('ru'), '')

    def test_get_for_select_locale_fallback(self):
        EaSignalForm.objects.create(
            code='AN_4_20_ACTIVE', name='4-20 мА, активный', category='analog')
        opts = EaSignalForm.get_for_select(locale='en')
        self.assertEqual(len(opts), 1)
        self.assertEqual(opts[0]['name'], '4-20 мА, активный')  # en нет → ru

    def test_copy_generates_unique_code_suffix(self):
        form = EaSignalForm.objects.create(
            code='DRY_SPST', name='Сухой контакт SPST', category='contact')
        copy_obj = form.copy()
        self.assertNotEqual(copy_obj.pk, form.pk)
        self.assertEqual(copy_obj.code, 'DRY_SPST Копия')


class EaControlSignalTests(TestCase):
    def setUp(self):
        self.disc_ac = EaSignalForm.objects.create(
            code='DISC_AC', name='Дискретный AC', category='discrete')
        self.an_passive = EaSignalForm.objects.create(
            code='AN_4_20_PASSIVE', name='4-20 мА пассивный', category='analog')

    def test_discrete_command_requires_discrete_form(self):
        sig = EaControlSignal(
            role='CMD_OCS', category='discrete', form=self.an_passive,
            code='BAD', name='Плохая команда')
        with self.assertRaises(ValidationError):
            sig.full_clean()

    def test_analog_command_requires_analog_form(self):
        sig = EaControlSignal(
            role='CMD_4_20MA', category='analog', form=self.disc_ac,
            code='BAD2', name='Плохая уставка')
        with self.assertRaises(ValidationError):
            sig.full_clean()

    def test_hart_allowed_only_on_analog(self):
        sig = EaControlSignal(
            role='CMD_OCS', category='discrete', form=self.disc_ac,
            voltage=220, code='CMD_TEST', name='Команда', hart=True)
        with self.assertRaises(ValidationError):
            sig.full_clean()


class EaFeedbackSignalTests(TestCase):
    def setUp(self):
        self.dry_spdt = EaSignalForm.objects.create(
            code='DRY_SPDT', name='Сухой контакт SPDT', category='contact')
        self.pot = EaSignalForm.objects.create(
            code='RES_POTENTIOMETER', name='Потенциометр', category='resistance')

    def test_potentiometer_requires_resistance(self):
        sig = EaFeedbackSignal(
            role='POSITION', category='analog', form=self.pot,
            code='FB_POT', name='Потенциометр без R')
        with self.assertRaises(ValidationError):
            sig.full_clean()

    def test_contact_normal_only_for_contacts(self):
        sig = EaFeedbackSignal(
            role='POSITION', category='analog', form=self.pot,
            resistance_kohm=5, code='FB_POT2', name='Потенциометр',
            contact_normal='NC')
        with self.assertRaises(ValidationError):
            sig.full_clean()

    def test_contact_signal_with_normal(self):
        sig = EaFeedbackSignal.objects.create(
            role='OVERHEAT', category='contact', form=self.dry_spdt,
            contact_normal='CHANGEOVER', max_voltage=250, max_current=5,
            code='FB_OVERHEAT', name='Перегрев SPDT')
        self.assertEqual(sig.contact_normal, 'CHANGEOVER')
        self.assertEqual(sig.name_i18n.get('ru'), 'Перегрев SPDT')

    def test_hart_on_resistance_form_rejected(self):
        sig = EaFeedbackSignal(
            role='POSITION', category='analog', form=self.pot,
            resistance_kohm=5, code='FB_POT3', name='Потенциометр', hart=True)
        with self.assertRaises(ValidationError):
            sig.full_clean()


class ControlUnitExtensionTests(TestCase):
    """Расширение ControlUnitInstalledOption полями фазы 3."""

    def setUp(self):
        self.form = EaSignalForm.objects.create(
            code='DISC_DC', name='Дискретный DC', category='discrete')
        self.signal = EaControlSignal.objects.create(
            role='CMD_OCS', category='discrete', form=self.form,
            voltage=24, code='CMD_TEST', name='Команда 24DC')
        self.protocol = EaCommProtocol.objects.create(
            code='PROTO_TEST', name='Тест-шина', transport='rs485')

    def test_kind_default_none(self):
        cu = ControlUnitInstalledOption.objects.create(
            code='CU-TEST-1', name='Тестовый БУ')
        self.assertEqual(cu.kind, 'NONE')

    def test_kind_choices_backfill_values(self):
        cu = ControlUnitInstalledOption.objects.create(
            code='int-x', name='INT/X', kind='INTEGRATED')
        self.assertEqual(cu.kind, 'INTEGRATED')
        self.assertIn('POSITIONER', dict(ControlUnitInstalledOption._meta
                                          .get_field('kind').choices))

    def test_m2m_related_names(self):
        cu = ControlUnitInstalledOption.objects.create(
            code='CU-TEST-2', name='Тестовый БУ 2', kind='INTEGRATED')
        cu.accepts.add(self.signal)
        cu.protocols.add(self.protocol)
        self.assertIn(cu, self.signal.accepting_control_units.all())
        self.assertIn(cu, self.protocol.control_units.all())
        self.assertEqual(list(cu.accepts.values_list('code', flat=True)), ['CMD_TEST'])


class EaSignalResolverTests(TestCase):
    """Резолвер матрицы: наследование, слоты, na, bundle, режим, конфликты, схемы."""

    def setUp(self):
        from producers.models import Brands
        from params.models import PowerSupplies
        from electric_actuators.models import (
            ElectricActuatorModelLine, ElectricActuatorModelLineItem,
            EaSignalMatrixEntry, EaWiringDiagramBinding, EaSignalSlot,
        )
        self.brand = Brands.objects.create(name='AOX', code='AOX')
        self.line = ElectricActuatorModelLine.objects.create(
            name='Серия R', description='', code='AR', brand=self.brand)
        self.item = ElectricActuatorModelLineItem.objects.create(
            name='Модель 005', description='', code='005', model_line=self.line)
        self.cu = ControlUnitInstalledOption.objects.create(
            code='CU-BASIC', name='Basic')
        self.ps = PowerSupplies.objects.create(
            name='220 В AC', code='220AC', encoding='', description='',
            voltage_value=220)
        self.slot_pos = EaSignalSlot.objects.create(
            code='POSITION_FEEDBACK', name='Позиционная ОС')
        self.slot_lim = EaSignalSlot.objects.create(
            code='LIMIT_SWITCHES', name='Концевые')
        self.pot_form = EaSignalForm.objects.create(
            code='RES_POT', name='Потенциометр', category='resistance')
        self.loop_form = EaSignalForm.objects.create(
            code='AN_4_20_P', name='4-20 пассивный', category='analog')
        self.pot = EaFeedbackSignal.objects.create(
            role='POSITION', category='analog', form=self.pot_form,
            resistance_kohm=1, code='FB_POT', name='Потенциометр')
        self.loop = EaFeedbackSignal.objects.create(
            role='POSITION', category='analog', form=self.loop_form,
            code='FB_LOOP', name='4-20 мА')

    def _resolve(self):
        from electric_actuators.services.ea_signal_resolver import resolve_matrix
        return resolve_matrix(self.item, self.cu, self.ps, 'on_off')

    def _row(self, **kw):
        defaults = dict(
            brand=self.brand, control_unit=self.cu, power_supply=self.ps,
            mode='both', slot=self.slot_pos, availability='opt')
        defaults.update(kw)
        return EaSignalMatrixEntry.objects.create(**defaults)

    def test_brand_rows_and_default(self):
        self._row(feedback_signal=self.pot)
        self._row(feedback_signal=self.loop, availability='std', is_default=True)
        res = self._resolve()
        self.assertEqual(len(res['slots']), 1)
        rows = res['slots'][0]['rows']
        self.assertEqual(len(rows), 2)
        self.assertEqual(res['defaults'], {self.slot_pos.pk: rows[0]['id']})
        self.assertIn('(Стандарт)', rows[0]['name'])

    def test_na_override_on_model_line(self):
        self._row(feedback_signal=self.pot)
        EaSignalMatrixEntry.objects.create(
            model_line=self.line, control_unit=self.cu, power_supply=self.ps,
            mode='both', slot=self.slot_pos, feedback_signal=self.pot,
            availability='na')
        res = self._resolve()
        self.assertEqual(res['slots'], [])

    def test_slot_single_choice_validation(self):
        r1 = self._row(feedback_signal=self.pot)
        r2 = self._row(feedback_signal=self.loop)
        from electric_actuators.services.ea_signal_resolver import validate_selection
        res = self._resolve()
        self.assertEqual(validate_selection([r1.pk, r2.pk], resolved=res), [
            f'В слоте {self.slot_pos.pk} выбрано больше одной строки: '
            f'{[r1.pk, r2.pk]}'])
        self.assertEqual(validate_selection([r1.pk], resolved=res), [])

    def test_bundle_atomicity(self):
        none_row = EaSignalMatrixEntry.objects.create(
            brand=self.brand, control_unit=self.cu, power_supply=self.ps,
            mode='both', slot=self.slot_lim, availability='std',
            bundle='MWG', name='Без переключателей')
        pos_row = self._row(feedback_signal=self.loop, availability='std',
                            bundle='MWG')
        res = self._resolve()
        self.assertEqual(set(res['bundles']['MWG']), {none_row.pk, pos_row.pk})
        # запрет строки позиции на уровне серии → пакет удаляется целиком
        EaSignalMatrixEntry.objects.create(
            model_line=self.line, control_unit=self.cu, power_supply=self.ps,
            mode='both', slot=self.slot_pos, feedback_signal=self.loop,
            availability='na')
        res2 = self._resolve()
        self.assertEqual(res2['slots'], [])
        self.assertTrue(any('MWG' in w for w in res2['warnings']))

    def test_mode_filter(self):
        self._row(feedback_signal=self.pot, mode='modulating')
        self.assertEqual(self._resolve()['slots'], [])
        from electric_actuators.services.ea_signal_resolver import resolve_matrix
        res = resolve_matrix(self.item, self.cu, self.ps, 'modulating')
        self.assertEqual(len(res['slots']), 1)

    def test_conflicts(self):
        r1 = self._row(feedback_signal=self.pot)
        r2 = self._row(feedback_signal=self.loop)
        r1.conflicts.add(r2)
        from electric_actuators.services.ea_signal_resolver import validate_selection
        res = self._resolve()
        self.assertEqual(len(res['conflicts']), 1)
        errors = validate_selection([r1.pk, r2.pk], resolved=res)
        self.assertTrue(any('Конфликт' in e for e in errors))

    def test_find_diagram_binding(self):
        from electric_actuators.services.ea_signal_resolver import find_diagram_binding
        r1 = self._row(feedback_signal=self.pot)
        r2 = self._row(feedback_signal=self.loop, slot=self.slot_lim)
        binding = EaWiringDiagramBinding.objects.create(
            model_line=self.line, control_unit=self.cu, power_supply=self.ps,
            name='Схема станд.')
        binding.signals.set([r1, r2])
        found = find_diagram_binding(
            self.item, self.cu, self.ps, 'on_off', [r1.pk, r2.pk])
        self.assertEqual(found, binding)
        self.assertIsNone(find_diagram_binding(
            self.item, self.cu, self.ps, 'on_off', [r1.pk]))

    def test_body_inheritance(self):
        """Строки скоупа «корпус» наследуются QUI-вариантами общего корпуса."""
        from electric_actuators.models import (ElectricActuatorBody,
            ElectricActuatorBodyTable, ElectricActuatorModelLineItem)
        from electric_actuators.services.ea_signal_resolver import resolve_matrix
        body = ElectricActuatorBody.objects.create(
            name='Корпус QUI', description='', model_line=self.line,
            body_table=ElectricActuatorBodyTable.objects.first())
        qui_item = ElectricActuatorModelLineItem.objects.create(
            name='AR01E005.QUI2.8/50', description='', code='005.QUI2.8/50',
            model_line=self.line, body=body)
        EaSignalMatrixEntry.objects.create(
            body=body, control_unit=self.cu, power_supply=self.ps,
            mode='both', slot=self.slot_pos, feedback_signal=self.pot,
            availability='std')
        res = resolve_matrix(qui_item, self.cu, self.ps, 'on_off')
        self.assertEqual(len(res['slots']), 1)
        self.assertEqual(res['slots'][0]['code'], 'POSITION_FEEDBACK')


class EaAdminMatrixIOTests(TestCase):
    """Экспорт/импорт матрицы в админке серии ЭП: кнопки на странице серии."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        from electric_actuators.models import ElectricActuatorModelLine
        from producers.models import Brands
        cls.superuser = get_user_model().objects.create_superuser(
            'ea_admin_test', 'ea@test.test', 'pass-12345')
        cls.brand = Brands.objects.create(name='AOX', code='AOX')
        cls.line = ElectricActuatorModelLine.objects.create(
            name='Серия AR', description='', code='AR', brand=cls.brand)

    def _client(self):
        from django.test import Client
        client = Client()
        client.force_login(self.superuser)
        return client

    def test_change_form_has_export_and_import_buttons(self):
        from django.urls import reverse
        url = reverse(
            'admin:electric_actuators_electricactuatormodelline_change',
            args=[self.line.pk])
        resp = self._client().get(url)
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode('utf-8', 'ignore')
        self.assertIn('export-signal-matrix', body)
        self.assertIn('import-signal-matrix', body)
        self.assertIn('Экспорт матрицы', body)
        self.assertIn('Импорт матрицы', body)

    def test_export_series_downloads_xlsx(self):
        from django.urls import reverse
        url = reverse('admin:electricactuatormodelline_export_matrix',
                      args=[self.line.pk])
        resp = self._client().get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['Content-Type'],
            'application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.sheet')
        self.assertIn('attachment;', resp['Content-Disposition'])

    def test_import_page_renders(self):
        from django.urls import reverse
        url = reverse('admin:electricactuatormodelline_import_matrix')
        resp = self._client().get(url)
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode('utf-8', 'ignore')
        self.assertIn('name="file"', body)
        self.assertIn('csrfmiddlewaretoken', body)


class EaCatalogExt1301Tests(TestCase):
    """Пакет 13.1: ввод кабелей, устройство на none-строке, temp-опции."""

    def test_connector_plug_rejects_gland_holes(self):
        from electric_actuators.models import CableGlandHolesSet
        from params.models import ThreadSize
        t = ThreadSize.objects.create(name='M20', code='M20')
        cg = CableGlandHolesSet(
            kind='CONNECTOR_PLUG', name='Разъём', cg1=t, text_description='x')
        with self.assertRaises(ValidationError):
            cg.full_clean()
        cg.cg1 = None
        cg.full_clean()  # без отверстий — валидно

    def test_device_on_none_row_with_name(self):
        from electric_actuators.models import (EaFeedbackDevice,
                                               EaSignalMatrixEntry, EaSignalSlot,
                                               ElectricActuatorModelLine,
                                               ElectricActuatorModelLineItem)
        from producers.models import Brands
        from params.models import ControlUnitInstalledOption, PowerSupplies
        brand = Brands.objects.create(name='AOX-T', code='AOX-T')
        line = ElectricActuatorModelLine.objects.create(
            name='Серия T', description='', code='T1', brand=brand)
        item = ElectricActuatorModelLineItem.objects.create(
            name='T1', description='', code='T1', model_line=line)
        dev = EaFeedbackDevice.objects.create(
            code='THERMAL_RELAY', name='Термореле', technology='BIMETAL',
            kind='THERMAL_SENSOR')
        slot = EaSignalSlot.objects.create(
            code='THERMAL_SENSOR', name='Датчик температуры')
        cu, _ = ControlUnitInstalledOption.objects.get_or_create(
            code='none', defaults={'name': 'нет'})
        ps, _ = PowerSupplies.objects.get_or_create(
            code='220-AC', defaults={'name': '220/50'})
        row = EaSignalMatrixEntry(
            model_line_item=item, slot=slot, mode='both',
            control_unit=cu, power_supply=ps,
            name='Датчик температуры без выхода ОС', device=dev,
            availability='opt')
        row.full_clean()  # none-строка с device и именем — валидна
        row2 = EaSignalMatrixEntry(
            model_line_item=item, slot=slot, mode='both',
            control_unit=cu, power_supply=ps, device=dev,
            availability='opt')
        with self.assertRaises(ValidationError):
            row2.full_clean()  # device без сигнала и без имени — ошибка

    def test_temperature_option_code_and_heater(self):
        from electric_actuators.models import (ElectricTemperatureOption,
                                               ElectricActuatorModelLine)
        from producers.models import Brands
        from params.models import ActuatorHeaterSupply
        brand = Brands.objects.create(name='AOX-T2', code='AOX-T2')
        line = ElectricActuatorModelLine.objects.create(
            name='Серия T2', description='', code='T2', brand=brand)
        hs, _ = ActuatorHeaterSupply.objects.get_or_create(
            code='SEPARATE_LINE', defaults={'name': 'От отдельной линии'})
        temp = ElectricTemperatureOption.objects.create(
            model_line=line, code='LT', heater_supply=hs,
            work_temp_min=-40, work_temp_max=70)
        self.assertEqual(temp.code, 'LT')
        self.assertEqual(temp.heater_supply.code, 'SEPARATE_LINE')


class EaMatrixFrameworkTests(TestCase):
    """Пакет 13.3: каркас выгрузки — все модели, пустые ячейки, is_default."""

    @classmethod
    def setUpTestData(cls):
        from electric_actuators.models import (
            EaSignalMatrixEntry, EaSignalSlot, EaSlotOption, EaFeedbackSignal,
            EaSignalForm, ElectricActuatorModelLine,
            ElectricActuatorModelLineItem, ElectricActuatorBody,
            ElectricActuatorBodyTable)
        from producers.models import Brands
        from params.models import ControlUnitInstalledOption, PowerSupplies
        cls.brand = Brands.objects.create(name='AOX-F', code='AOX-F')
        cls.line = ElectricActuatorModelLine.objects.create(
            name='Серия F', description='', code='TF', brand=cls.brand)
        cls.cu, _ = ControlUnitInstalledOption.objects.get_or_create(
            code='none', defaults={'name': 'нет'})
        cls.ps, _ = PowerSupplies.objects.get_or_create(
            code='220-AC', defaults={'name': '220/50'})
        cls.slot = EaSignalSlot.objects.create(
            code='LIMIT_SWITCHES', name='Концевые')
        form = EaSignalForm.objects.create(
            code='DRY_SPDT', name='SPDT', category='contact')
        cls.sig = EaFeedbackSignal.objects.create(
            role='END_OPEN', category='contact', form=form,
            code='FB_END_OPEN_SPDT', name='Конечное Открыто SPDT')
        cls.opt = EaSlotOption.objects.create(
            code='LIMIT_SWITCHES:FB_END_OPEN_SPDT', slot=cls.slot,
            kind='signal', feedback_signal=cls.sig, name='Концевое SPDT')
        table = ElectricActuatorBodyTable.objects.first()
        cls.body1 = ElectricActuatorBody.objects.create(
            name='Корпус F1', description='', model_line=cls.line,
            body_table=table)
        cls.body2 = ElectricActuatorBody.objects.create(
            name='Корпус F2', description='', model_line=cls.line,
            body_table=table)
        cls.item1 = ElectricActuatorModelLineItem.objects.create(
            name='F1', description='', code='F1', model_line=cls.line,
            body=cls.body1)
        cls.item2 = ElectricActuatorModelLineItem.objects.create(
            name='F2', description='', code='F2', model_line=cls.line,
            body=cls.body2)
        EaSignalMatrixEntry.objects.create(
            body=cls.body1, control_unit=cls.cu, power_supply=cls.ps,
            mode='on_off', slot=cls.slot, feedback_signal=cls.sig,
            option=cls.opt, availability='std')

    def test_framework_covers_items_with_pairs(self):
        from electric_actuators.services.ea_matrix_io import export_series_rows
        rows = export_series_rows('TF')
        item_codes = {r['item_code'] for r in rows}
        # пары per-модель: F1 имеет матричную строку, F2 — без пар → нет строк
        self.assertEqual(item_codes, {'F1'})
        r1 = [r for r in rows if r['item_code'] == 'F1'
              and r['option_code'] == 'LIMIT_SWITCHES:FB_END_OPEN_SPDT']
        r2 = [r for r in rows if r['item_code'] == 'F2'
              and r['option_code'] == 'LIMIT_SWITCHES:FB_END_OPEN_SPDT']
        self.assertEqual(len(r1), 1)
        self.assertEqual(r1[0]['availability'], 'std')
        self.assertTrue(r1[0]['is_default'])  # std → default
        self.assertEqual(r2, [])

    def test_import_skips_empty_cells(self):
        from electric_actuators.services.ea_matrix_io import (
            export_series_rows, apply_import)
        rows = export_series_rows('TF')
        stats = apply_import(rows)
        self.assertEqual(stats['errors'], [])
        # пустые ячейки пропущены: обновлена только существующая std-строка
        self.assertEqual(stats['created'], 0)
        self.assertEqual(stats['updated'], 1)

    def test_import_two_none_options_same_slot(self):
        """Ревью №7 F1: две none-опции одного слота не затирают друг друга."""
        from electric_actuators.models import (EaSignalSlot, EaSlotOption,
                                               EaSignalMatrixEntry)
        from electric_actuators.services.ea_matrix_io import apply_import
        ind = EaSignalSlot.objects.create(code='INDICATOR', name='Индикация')
        EaSlotOption.objects.create(
            code='INDICATOR:LED_SET', slot=ind, kind='none',
            name='Светодиодный набор')
        EaSlotOption.objects.create(
            code='INDICATOR:BLINKER', slot=ind, kind='none', name='Блинкер')
        base = dict(series_code='TF', item_code='F1', body_code='Корпус F1',
                    control_unit='none', power_supply='220-AC', mode='on_off',
                    slot='INDICATOR', kind='none', signal_code='',
                    form_code='', heater_supply='', availability='opt',
                    is_default=False, bundle='', device='', encoding='',
                    ext_encoding='')
        stats = apply_import([
            dict(base, option_code='INDICATOR:LED_SET'),
            dict(base, option_code='INDICATOR:BLINKER')])
        self.assertEqual(stats['errors'], [])
        self.assertEqual(stats['created'], 2)
        rows = EaSignalMatrixEntry.objects.filter(slot=ind)
        self.assertEqual(rows.count(), 2)
        self.assertEqual({r.name for r in rows},
                         {'Светодиодный набор', 'Блинкер'})


class EaExtCodeTests(TestCase):
    """Пакет 14: расширенный код — правила, сборка, расшифровка."""

    @classmethod
    def setUpTestData(cls):
        from electric_actuators.models import (
            EaSignalSlot, EaSlotOption, EaFeedbackSignal, EaSignalForm,
            EaControlSignal, ElectricActuatorModelLine,
            AllowedControlUnitOption, ElectricTemperatureOption,
        )
        from producers.models import Brands
        from params.models import (ControlUnitInstalledOption, PowerSupplies,
                                   ActuatorHeaterSupply)
        cls.brand = Brands.objects.create(name='AOX-X', code='AOX-X')
        cls.line = ElectricActuatorModelLine.objects.create(
            name='Серия X', description='', code='TX', brand=cls.brand)
        cls.cu_int, _ = ControlUnitInstalledOption.objects.get_or_create(
            code='int-o', defaults={'name': 'INT/O'})
        cls.ps220, _ = PowerSupplies.objects.get_or_create(
            code='220-AC', defaults={'name': '220/50'})
        PowerSupplies.objects.get_or_create(code='380-AC',
                                            defaults={'name': '380/50'})
        PowerSupplies.objects.get_or_create(code='24-DC',
                                            defaults={'name': '24DC'})
        AllowedControlUnitOption.objects.create(
            model_line=cls.line, control_unit=cls.cu_int,
            power_supply=cls.ps220, encoding='INT/O',
            ext_encoding='IO', is_active=True)
        no_heater, _ = ActuatorHeaterSupply.objects.get_or_create(
            code='NO_HEATER', defaults={'name': 'Нет обогрева'})
        sep, _ = ActuatorHeaterSupply.objects.get_or_create(
            code='SEPARATE_LINE', defaults={'name': 'Отдельная линия'})
        motor, _ = ActuatorHeaterSupply.objects.get_or_create(
            code='MOTOR_CIRCUIT', defaults={'name': 'От цепей устройства'})
        ElectricTemperatureOption.objects.create(
            model_line=cls.line, code='STD', heater_supply=no_heater,
            is_default=True, work_temp_min=-20, work_temp_max=70)
        ElectricTemperatureOption.objects.create(
            model_line=cls.line, code='LT', heater_supply=sep,
            work_temp_min=-40, work_temp_max=70)
        ElectricTemperatureOption.objects.create(
            model_line=cls.line, code='LT', heater_supply=motor,
            work_temp_min=-40, work_temp_max=70)
        slot_lim = EaSignalSlot.objects.create(
            code='LIMIT_SWITCHES', name='Концевые')
        EaSlotOption.objects.create(
            code='LIMIT_SWITCHES:END_SPDT', slot=slot_lim, kind='pair',
            name='Концевые SPDT')
        slot_th = EaSignalSlot.objects.create(
            code='THERMAL_SENSOR', name='Теплозащита')
        form = EaSignalForm.objects.create(
            code='DRY_SPST', name='SPST', category='contact')
        sig_nc = EaFeedbackSignal.objects.create(
            role='OVERHEAT', category='contact', form=form,
            code='FB_OVERHEAT_NC', name='Перегрев НЗ')
        EaSlotOption.objects.create(
            code='THERMAL_SENSOR:FB_OVERHEAT_NC', slot=slot_th, kind='signal',
            feedback_signal=sig_nc, name='Перегрев НЗ')
        # Позиции op-блока для теста однозначности кодов
        slot_ind = EaSignalSlot.objects.create(code='INDICATOR', name='Индикация')
        for code, name in (('LED_SET', 'Светодиодный набор'),
                           ('BLINKER', 'Блинкер'),
                           ('LED_SET_BLINKER', 'Светодиоды + блинкер')):
            EaSlotOption.objects.create(
                code=f'INDICATOR:{code}', slot=slot_ind, kind='none', name=name)
        slot_cmd = EaSignalSlot.objects.create(code='CMD', name='Команды')
        form_dc = EaSignalForm.objects.create(
            code='DISC_DC', name='Дискретная цепь DC', category='discrete')
        ctrl_dc = EaControlSignal.objects.create(
            role='CMD_OCS', category='discrete', form=form_dc,
            code='CMD_OCS_24DC', name='Команда О/С/З 24 В DC')
        EaSlotOption.objects.create(
            code='CMD:CMD_OCS_24DC', slot=slot_cmd, kind='control',
            control_signal=ctrl_dc, name='О/С/З 24 В DC')

    def test_coding_rules_structure(self):
        from electric_actuators.services.ea_ext_code import coding_rules
        rules = coding_rules(self.line)
        self.assertEqual(len(rules), 5)
        self.assertEqual([b['key'] for b in rules],
                         ['bu', 'sw', 'fb', 'cl', 'op'])
        cu_opts = {o['code'] for o in rules[0]['positions'][0]['options']}
        self.assertIn('IO', cu_opts)
        temp_opts = {o['code']
                     for b in rules for p in b['positions']
                     if p['key'] == 'temp' for o in p['options']}
        self.assertIn('L', temp_opts)
        self.assertIn('LM', temp_opts)

    def test_build_decode_roundtrip(self):
        from electric_actuators.services.ea_ext_code import (
            build_ext_code, decode_ext_code)
        selection = {'cu': 'IO', 'cu_p': 'X', 'ps': '3', 'mode': 'M',
                     'end': 'E1', 'temp': 'LM', 'therm': 'T1'}
        code = build_ext_code(self.line, selection)
        self.assertIn('IOX3M', code)
        self.assertIn('E1', code)
        self.assertIn('LMT1', code)
        decoded, warnings = decode_ext_code(self.line, code)
        self.assertEqual(warnings, [])
        for pos, sel_code in selection.items():
            self.assertEqual(decoded[pos]['code'], sel_code, pos)
        # обратная сборка даёт тот же код
        rebuilt = build_ext_code(
            self.line, {p: d['code'] for p, d in decoded.items()})
        self.assertEqual(rebuilt, code)

    def test_build_validation(self):
        from electric_actuators.services.ea_ext_code import build_ext_code
        with self.assertRaises(ValueError):
            build_ext_code(self.line, {'cu': 'ZZ'})  # неизвестный код
        with self.assertRaises(ValueError):
            build_ext_code(self.line, {'cu_p': 'X'})  # питание БУ без БУ

    def test_decode_op_block_unambiguous(self):
        """Ревью №7 F2: 'DB' — индикация LED+блинкер, а не cmd+ind."""
        from electric_actuators.services.ea_ext_code import (
            build_ext_code, decode_ext_code)
        code_db = build_ext_code(self.line, {'ind': 'DB'})
        decoded, warnings = decode_ext_code(self.line, code_db)
        self.assertEqual(decoded['ind']['code'], 'DB')
        self.assertEqual(decoded['cmd']['code'], '')
        code_dc = build_ext_code(self.line, {'cmd': 'DC'})
        decoded2, warnings2 = decode_ext_code(self.line, code_dc)
        self.assertEqual(decoded2['cmd']['code'], 'DC')
        self.assertEqual(decoded2['ind']['code'], '')

    def test_configurator_data_and_ext_from_rows(self):
        """Фаза 6: слоты конфигуратора + ext-код из выбранных строк матрицы."""
        from electric_actuators.models import (
            EaSignalMatrixEntry, EaFeedbackSignal, EaSignalForm, EaSlotOption,
            ElectricActuatorBody, ElectricActuatorBodyTable,
            ElectricActuatorModelLineItem, ElectricTemperatureOption,
        )
        from electric_actuators.services.ea_configurator_data import (
            configurator_signal_data, selection_ext_code)
        table = ElectricActuatorBodyTable.objects.first()
        body = ElectricActuatorBody.objects.create(
            name='Корпус X1', description='', model_line=self.line,
            body_table=table)
        item = ElectricActuatorModelLineItem.objects.create(
            name='X1', description='', code='X1', model_line=self.line,
            body=body)
        form_spdt, _ = EaSignalForm.objects.get_or_create(
            code='DRY_SPDT', defaults={'name': 'SPDT', 'category': 'contact'})
        for code, role, name in (('FB_END_OPEN_SPDT', 'END_OPEN',
                                  'Конечное Открыто SPDT'),
                                 ('FB_END_CLOSE_SPDT', 'END_CLOSE',
                                  'Конечное Закрыто SPDT')):
            EaFeedbackSignal.objects.get_or_create(
                code=code, defaults={'role': role, 'category': 'contact',
                                     'form': form_spdt, 'name': name})
        option = EaSlotOption.objects.get(code='LIMIT_SWITCHES:END_SPDT')
        for sig_code in ('FB_END_OPEN_SPDT', 'FB_END_CLOSE_SPDT'):
            EaSignalMatrixEntry.objects.create(
                body=body, control_unit=self.cu_int, power_supply=self.ps220,
                mode='on_off', slot=option.slot, option=option,
                feedback_signal=EaFeedbackSignal.objects.get(code=sig_code),
                availability='std', bundle='END_SPDT:X1:on_off')
        data = configurator_signal_data(item, self.cu_int, self.ps220,
                                        'on_off')
        lim = [s for s in data['slots'] if s['code'] == 'LIMIT_SWITCHES'][0]
        self.assertEqual(len(lim['rows']), 2)
        self.assertTrue(all(r['ext'] == 'end=E1' for r in lim['rows']))
        row_ids = [r['id'] for r in lim['rows']]
        code = selection_ext_code(item, row_ids)
        self.assertIn('E1', code)
        temp = ElectricTemperatureOption.objects.get(
            model_line=self.line, code='LT',
            heater_supply__code='SEPARATE_LINE')
        code2 = selection_ext_code(item, row_ids, temp_option=temp,
                                   context={'cu': 'IO'})
        self.assertIn('E1', code2)
        self.assertIn('L', code2)


class Phase7LegacyRemovalSmokeTests(TestCase):
    """Фаза 7: конструктор/админки/API не должны падать после удаления
    сигнальных через-опций (ревью №8, F1–F7)."""

    @classmethod
    def setUpTestData(cls):
        from producers.models import Brands
        from electric_actuators.models import (ElectricActuatorModelLine,
                                               ElectricActuatorModelLineItem,
                                               ElectricActuatorConstructor)
        cls.brand = Brands.objects.create(name='SMOKE-B', code='SMOKE-B')
        cls.line = ElectricActuatorModelLine.objects.create(
            name='Серия SMOKE', description='', code='SMK', brand=cls.brand)
        cls.mli = ElectricActuatorModelLineItem.objects.create(
            model_line=cls.line, name='SMOKE-ITEM', code='SMKI')
        cls.constructor = ElectricActuatorConstructor.objects.create(
            name='SMOKE-C', code='SMK-C', selected_model_line_item=cls.mli)

    def test_constructor_save_generates_description(self):
        """save() не должен падать на удалённых полях в get_description_data."""
        from electric_actuators.models import ElectricActuatorConstructor
        c = ElectricActuatorConstructor(name='smoke-new', code='SMK-N')
        c.save()
        self.assertTrue(c.pk)
        self.assertIsInstance(c.description, str)

    def test_description_and_structured_data_clean(self):
        c = self.constructor
        self.assertIsInstance(c.description, str)
        structured = c.get_structured_data()
        for removed in ('blinker', 'mechanical_indicator', 'end_switches',
                        'way_switches', 'torque_switches'):
            self.assertNotIn(removed, structured['selected_options'])

    def test_get_available_options_with_mli(self):
        from electric_actuators.models import ElectricActuatorConstructor
        opts = ElectricActuatorConstructor(
            selected_model_line_item=self.mli).get_available_options()
        self.assertIsInstance(opts, dict)
        for removed in ('blinker_options', 'mechanical_indicator_options',
                        'end_switches_options', 'way_switches_options',
                        'torque_switches_options', 'control_unit_options'):
            self.assertNotIn(removed, opts)

    def test_create_duplicate(self):
        dup = self.constructor.create_duplicate()
        self.assertTrue(dup.pk)

    def test_constructor_admin_form_builds(self):
        from django.contrib import admin
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        from electric_actuators.admin import ElectricActuatorConstructorAdmin
        from electric_actuators.models import ElectricActuatorConstructor
        req = RequestFactory().get('/admin/')
        req.user = AnonymousUser()
        ma = ElectricActuatorConstructorAdmin(
            ElectricActuatorConstructor, admin.site)
        self.assertTrue(ma.get_form(req)())

    def test_selected_admin_form_builds(self):
        from django.contrib import admin
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        from electric_actuators.admin import ElectricActuatorSelectedAdmin
        from electric_actuators.models import ElectricActuatorSelected
        req = RequestFactory().get('/admin/')
        req.user = AnonymousUser()
        ma = ElectricActuatorSelectedAdmin(ElectricActuatorSelected, admin.site)
        self.assertTrue(ma.get_form(req)())

    def test_constructor_viewset_serializes(self):
        from electric_actuators.api.views_constructor import ConstructorViewSet
        vs = ConstructorViewSet()

        class R:
            user = None
            query_params = {}

        vs.request = R()
        qs = vs.get_queryset()
        list(qs[:1])  # select_related без удалённых полей
        data = vs._serialize(self.constructor)
        self.assertEqual(data['id'], self.constructor.id)


class AllowedCuAndIndicatorTests(TestCase):
    """Модельные перекрытия AllowedControlUnitOption и INDICATOR-правило
    бренда (заливка правил пользователя 2026-10-18)."""

    @classmethod
    def setUpTestData(cls):
        from producers.models import Brands
        from params.models import ControlUnitInstalledOption, PowerSupplies
        from electric_actuators.models import (ElectricActuatorModelLine,
                                               ElectricActuatorModelLineItem,
                                               AllowedControlUnitOption)
        cls.brand = Brands.objects.create(name='T-B', code='T-B')
        cls.line = ElectricActuatorModelLine.objects.create(
            name='Серия T', description='', code='TA', brand=cls.brand)
        cls.m1 = ElectricActuatorModelLineItem.objects.create(
            model_line=cls.line, name='M1', code='M1')
        cls.m2 = ElectricActuatorModelLineItem.objects.create(
            model_line=cls.line, name='M2', code='M2')
        cls.cu_int, _ = ControlUnitInstalledOption.objects.get_or_create(
            code='int-t', defaults={'name': 'INT/T', 'kind': 'INTEGRATED'})
        if cls.cu_int.kind != 'INTEGRATED':
            cls.cu_int.kind = 'INTEGRATED'
            cls.cu_int.save(update_fields=['kind'])
        cls.cu_basic, _ = ControlUnitInstalledOption.objects.get_or_create(
            code='basic', defaults={'name': 'Basic', 'kind': 'BASIC'})
        if cls.cu_basic.kind != 'BASIC':
            cls.cu_basic.kind = 'BASIC'
            cls.cu_basic.save(update_fields=['kind'])
        cls.ps220, _ = PowerSupplies.objects.get_or_create(
            code='220-AC', defaults={'name': '220/50'})
        cls.ps380, _ = PowerSupplies.objects.get_or_create(
            code='380-AC', defaults={'name': '380/50'})
        AllowedControlUnitOption.objects.create(
            model_line=cls.line, control_unit=cls.cu_int,
            power_supply=cls.ps380, encoding='INT/T', is_active=True)
        AllowedControlUnitOption.objects.create(
            model_line=cls.line, control_unit=cls.cu_basic,
            power_supply=cls.ps380, encoding='', is_active=True)
        # Запрет basic×380 для M1 (модельное перекрытие)
        AllowedControlUnitOption.objects.create(
            model_line=cls.line, control_unit=cls.cu_basic,
            power_supply=cls.ps380, model_line_item=cls.m1,
            encoding='', is_active=False)
        # Запрет пары для модели M1 (перекрытие серийной строки)
        AllowedControlUnitOption.objects.create(
            model_line=cls.line, control_unit=cls.cu_int,
            power_supply=cls.ps380, model_line_item=cls.m1,
            encoding='INT/T', is_active=False)
        # Слот+опция — чтобы каркас экспорта не был пустым
        from electric_actuators.models import EaSignalSlot, EaSlotOption
        cls.slot = EaSignalSlot.objects.create(
            code='LIMIT_SWITCHES3', name='Концевые3')
        EaSlotOption.objects.create(
            code='LIMIT_SWITCHES3:END_SPDT', slot=cls.slot, kind='pair',
            name='Концевые SPDT')

    def test_resolve_cu_pair_model_override(self):
        from electric_actuators.models.ea_allowed_options import resolve_cu_pair
        self.assertIsNone(resolve_cu_pair(self.line, self.m1, self.cu_int,
                                          self.ps380))
        self.assertIsNotNone(resolve_cu_pair(self.line, self.m2, self.cu_int,
                                             self.ps380))
        # пара (БУ×220) вообще не объявлена — недоступна для любой модели
        self.assertIsNone(resolve_cu_pair(self.line, self.m1, self.cu_int,
                                          self.ps220))

    def test_export_pairs_respect_model_override(self):
        from electric_actuators.services.ea_matrix_io import export_series_rows
        rows = export_series_rows('TA')
        m1 = [r for r in rows if r['item_code'] == 'M1'
              and r['control_unit'] == 'int-t'
              and r['power_supply'] == '380-AC']
        m2 = [r for r in rows if r['item_code'] == 'M2'
              and r['control_unit'] == 'int-t'
              and r['power_supply'] == '380-AC']
        self.assertEqual(m1, [])
        self.assertTrue(m2)

    def test_indicator_brand_rule_resolves(self):
        """INDICATOR-строка бренда видна для модели любой серии бренда."""
        from params.models import ControlUnitInstalledOption, PowerSupplies
        from electric_actuators.models import (EaSignalSlot, EaSlotOption,
                                               EaSignalMatrixEntry)
        from electric_actuators.services.ea_signal_resolver import resolve_matrix
        none, _ = ControlUnitInstalledOption.objects.get_or_create(
            code='none-t', defaults={'name': 'нет-t'})
        slot = EaSignalSlot.objects.create(code='INDICATOR2', name='Индикация2')
        opt = EaSlotOption.objects.create(
            code='INDICATOR2:BLINKER', slot=slot, kind='none',
            name='Блинкер')
        EaSignalMatrixEntry.objects.create(
            brand=self.brand, control_unit=none, power_supply=self.ps220,
            mode='both', slot=slot, option=opt, availability='std',
            name='Блинкер', is_default=True)
        res = resolve_matrix(self.m1, none, self.ps220, 'on_off')
        rows = []
        for s in res['slots']:
            if s['code'] == 'INDICATOR2':
                rows = s['rows']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['availability'], 'std')
        self.assertTrue(rows[0]['is_default'])

    def test_wide_export_no_and_heater_rules(self):
        """Широкий формат: запрещённая пара БУ×напряжение → 'no';
        обогрев БУ по kind (BASIC/NONE → 'no', INTEGRATED → по данным)."""
        from electric_actuators.services.ea_matrix_io import export_wide_rows
        headers, rows = export_wide_rows('TA')
        m1_380 = [r for r in rows if r['item_code'] == 'M1'
                  and r['power_supply'] == '380-AC'][0]
        m2_380 = [r for r in rows if r['item_code'] == 'M2'
                  and r['power_supply'] == '380-AC'][0]
        # basic×380 запрещён для M1 → вся группа 'no'
        self.assertEqual(m1_380['basic|CMD_OCS_220AC'], 'no')
        self.assertEqual(m1_380['basic|FB_END_OPEN_SPDT'], 'no')
        self.assertEqual(m1_380['basic|heater|SEPARATE_LINE'], 'no')
        # для M2 пара доступна — данные пустые, но обогрева БУ нет (kind)
        self.assertEqual(m2_380['basic|CMD_OCS_220AC'], '')
        self.assertEqual(m2_380['basic|heater|SEPARATE_LINE'], 'no')
        self.assertEqual(m2_380['basic|heater|CU_CIRCUIT'], 'no')

    def test_constructor_ext_helpers(self):
        """ext-хелперы конструктора: cu/temp коды для шаблона ext_encoding."""
        from params.models import ControlUnitInstalledOption, \
            ActuatorHeaterSupply
        from electric_actuators.models import (ElectricActuatorConstructor,
                                               ElectricTemperatureOption)
        c = ElectricActuatorConstructor()
        self.assertEqual(c._cu_ext(), '')
        self.assertEqual(c._ps_ext(), '')
        self.assertEqual(c._temp_ext(), '')
        cu_io, _ = ControlUnitInstalledOption.objects.get_or_create(
            code='int-o', defaults={'name': 'INT/O'})
        c.selected_control_unit_option = cu_io
        self.assertEqual(c._cu_ext(), 'IO')
        motor, _ = ActuatorHeaterSupply.objects.get_or_create(
            code='MOTOR_CIRCUIT', defaults={'name': 'От цепей устройства'})
        t = ElectricTemperatureOption.objects.create(
            model_line=self.line, code='LT', heater_supply=motor)
        c.selected_temperature = t
        self.assertEqual(c._temp_ext(), 'LM')



