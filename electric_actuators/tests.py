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
    EaSignalFormCategory, EaControlSignalRole, EaFeedbackSignalRole,
    EaContactNormal, EaProtocolTransport,
)


def _cat(code):
    return EaSignalFormCategory.objects.get_or_create(
        code=code, defaults={'name': code})[0]


def _role(model_cls, code):
    return model_cls.objects.get_or_create(
        code=code, defaults={'name': code})[0]


def _normal(code):
    return EaContactNormal.objects.get_or_create(
        code=code, defaults={'name': code})[0]


def _transport(code):
    return EaProtocolTransport.objects.get_or_create(
        code=code, defaults={'name': code})[0]


class EaSignalFormTests(TestCase):
    def test_create_form_and_i18n_sync(self):
        form = EaSignalForm.objects.create(
            code='T-DRY_SPDT', name='Сухой контакт SPDT', category=_cat('contact'))
        self.assertEqual(form.name_i18n.get('ru'), 'Сухой контакт SPDT')
        self.assertEqual(form.description_i18n.get('ru'), '')

    def test_get_for_select_locale_fallback(self):
        EaSignalForm.objects.create(
            code='T-AN_4_20_ACTIVE', name='Тест-петля 4-20 мА', category=_cat('analog'))
        opts = EaSignalForm.get_for_select(locale='en')
        ours = [o for o in opts if o['name'] == 'Тест-петля 4-20 мА']
        self.assertEqual(len(ours), 1)  # en нет → ru

    def test_copy_generates_unique_code_suffix(self):
        form = EaSignalForm.objects.create(
            code='T-DRY_SPST', name='Сухой контакт SPST', category=_cat('contact'))
        copy_obj = form.copy()
        self.assertNotEqual(copy_obj.pk, form.pk)
        self.assertEqual(copy_obj.code, 'T-DRY_SPST Копия')


class EaControlSignalTests(TestCase):
    def setUp(self):
        self.disc_ac = EaSignalForm.objects.create(
            code='T-DISC_AC', name='Дискретный AC', category=_cat('discrete'))
        self.an_passive = EaSignalForm.objects.create(
            code='T-AN_4_20_PASSIVE', name='4-20 мА пассивный', category=_cat('analog'))

    def test_discrete_command_requires_discrete_form(self):
        sig = EaControlSignal(
            role=_role(EaControlSignalRole, 'CMD_OCS'), category='discrete',
            form=self.an_passive, code='BAD', name='Плохая команда')
        with self.assertRaises(ValidationError):
            sig.full_clean()

    def test_analog_command_requires_analog_form(self):
        sig = EaControlSignal(
            role=_role(EaControlSignalRole, 'CMD_4_20MA'), category='analog',
            form=self.disc_ac, code='BAD2', name='Плохая уставка')
        with self.assertRaises(ValidationError):
            sig.full_clean()

    def test_hart_allowed_only_on_analog(self):
        sig = EaControlSignal(
            role=_role(EaControlSignalRole, 'CMD_OCS'), category='discrete',
            form=self.disc_ac, voltage=220, code='CMD_TEST', name='Команда',
            hart=True)
        with self.assertRaises(ValidationError):
            sig.full_clean()


class EaFeedbackSignalTests(TestCase):
    def setUp(self):
        self.dry_spdt = EaSignalForm.objects.create(
            code='T-DRY_SPDT', name='Сухой контакт SPDT', category=_cat('contact'))
        self.pot = EaSignalForm.objects.create(
            code='T-RES_POTENTIOMETER', name='Потенциометр', category=_cat('resistance'))

    def test_potentiometer_requires_resistance(self):
        sig = EaFeedbackSignal(
            role=_role(EaFeedbackSignalRole, 'POSITION'), category='analog',
            form=self.pot, code='FB_POT', name='Потенциометр без R')
        with self.assertRaises(ValidationError):
            sig.full_clean()

    def test_contact_normal_only_for_contacts(self):
        sig = EaFeedbackSignal(
            role=_role(EaFeedbackSignalRole, 'POSITION'), category='analog',
            form=self.pot, resistance_kohm=5, code='FB_POT2',
            name='Потенциометр', contact_normal=_normal('NC'))
        with self.assertRaises(ValidationError):
            sig.full_clean()

    def test_contact_signal_with_normal(self):
        sig = EaFeedbackSignal.objects.create(
            role=_role(EaFeedbackSignalRole, 'OVERHEAT'), category='contact',
            form=self.dry_spdt, contact_normal=_normal('CHANGEOVER'),
            max_voltage=250, max_current=5,
            code='FB_OVERHEAT', name='Перегрев SPDT')
        self.assertEqual(sig.contact_normal.code, 'CHANGEOVER')
        self.assertEqual(sig.name_i18n.get('ru'), 'Перегрев SPDT')

    def test_hart_on_resistance_form_rejected(self):
        sig = EaFeedbackSignal(
            role=_role(EaFeedbackSignalRole, 'POSITION'), category='analog',
            form=self.pot, resistance_kohm=5, code='FB_POT3',
            name='Потенциометр', hart=True)
        with self.assertRaises(ValidationError):
            sig.full_clean()


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
                        'torque_switches_options'):
            self.assertNotIn(removed, opts)
        # слотовая модель: ключи БУ присутствуют всегда (пусто/без пакета)
        self.assertEqual(opts.get('control_unit_options'), [])
        self.assertIsNone(opts.get('control_unit_package'))

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

    def test_get_spec_sections_from_json_template(self):
        """Спека строится из JSON spec_template; пустые значения отбрасываются."""
        from core.models.equipment_type import EquipmentType
        from electric_actuators.models import ElectricActuatorConstructor
        et = EquipmentType.objects.get(code='electric-actuator')
        et.spec_template = {
            'Основные': {
                'Модель': 'model_code',
                'Серия': 'series_code',
                'Исполнение': 'body_code',
            },
        }
        et.save()
        c = ElectricActuatorConstructor(
            selected_model_line=self.line, selected_model_line_item=self.mli)
        spec = c._get_spec_sections()
        self.assertEqual(spec['Основные']['Модель'], 'SMKI')
        self.assertEqual(spec['Основные']['Серия'], 'SMK')
        # body_code пуст (у SMKI нет body) → ключ «Исполнение» не выводится
        self.assertNotIn('Исполнение', spec['Основные'])

    def test_cu_spec_groups_empty_without_control_unit(self):
        from electric_actuators.models import ElectricActuatorConstructor
        c = ElectricActuatorConstructor(
            selected_model_line=self.line, selected_model_line_item=self.mli)
        self.assertEqual(c._cu_spec_groups(), {})

    def test_preview_returns_spec(self):
        """preview отдаёт структурированную спеку (ключ spec)."""
        from core.models.equipment_type import EquipmentType
        from electric_actuators.api.views_constructor import ConstructorViewSet
        et = EquipmentType.objects.get(code='electric-actuator')
        et.spec_template = {'Основные': {'Модель': 'model_code'}}
        et.save()

        vs = ConstructorViewSet()

        class R:
            data = {'selected_model_line': self.line.id,
                    'selected_model_line_item': self.mli.id}
            headers = {}

        vs.request = R()
        resp = vs.preview(vs.request)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('spec', resp.data)
        self.assertEqual(resp.data['spec']['Основные']['Модель'], 'SMKI')

    def test_preview_and_spec_docx_routes_registered(self):
        """Роуты preview/spec-docx зарегистрированы (декоратор @action на месте)."""
        from django.urls import reverse
        self.assertEqual(
            reverse('ea-constructor-preview'),
            '/api/electric_actuators/constructor/preview/')
        self.assertEqual(
            reverse('ea-constructor-spec-docx'),
            '/api/electric_actuators/constructor/spec-docx/')
