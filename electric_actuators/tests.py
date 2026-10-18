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
