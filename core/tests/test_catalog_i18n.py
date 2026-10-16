"""
Тесты локализации spec_template/шаблонов серий и detail-вью каталогов.

Прогон — на копии рабочей БД (`test_db.sqlite3`, см. SESSION.md §8):
    python manage.py test core.tests.test_catalog_i18n --keepdb

Покрытие:
  - spec_template_i18n: карточки КВ через EquipmentType (общий паттерн), ПП-айтем через EquipmentType;
  - name_template_i18n: generate_name('en'/'cn') реального айтема;
  - detail-вью каталогов: локаль из Accept-Language;
  - идемпотентность команд-переводчиков (--dry-run, без записи).
"""
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase

from cable_glands.models import CableGland, CableGlandModelLine
from core.models import EquipmentType
from pneumatic_actuators.models import PneumaticActuatorModelLineItem
from pneumatic_fittings.models import (
    FittingShape, PneumaticSilencerModelLine, SilencerShape)
from solenoid_valves.models import DirectionValve


def _spec_labels(item, locale):
    """Плоский список (группа, подпись) из _get_spec_sections(locale)."""
    result = []
    for group, fields in item._get_spec_sections(locale=locale).items():
        result.append(group)
        result.extend(fields.keys())
    return result


class SpecTemplateI18nTests(TestCase):
    """spec_template_i18n: карточки через EquipmentType (общий паттерн)."""

    def test_cable_gland_spec_sections_en(self):
        item = CableGland.objects.filter(is_active=True).first()
        self.assertIsNotNone(item)
        labels = _spec_labels(item, 'en')
        self.assertIn('General', labels)
        self.assertIn('Connections', labels)
        self.assertIn('Thread', labels)
        self.assertNotIn('Основные', labels)

    def test_cable_gland_spec_sections_ru_default(self):
        item = CableGland.objects.filter(is_active=True).first()
        labels = _spec_labels(item, None)
        self.assertIn('Основные', labels)
        self.assertNotIn('General', labels)

    def test_cable_gland_spec_sections_cn(self):
        item = CableGland.objects.filter(is_active=True).first()
        labels = _spec_labels(item, 'cn')
        self.assertIn('基本参数', labels)
        self.assertNotIn('Основные', labels)

    def test_pa_item_spec_sections_via_equipment_type(self):
        """У серий ПП шаблона нет — берётся EquipmentType «Пневмопривод» (en)."""
        item = PneumaticActuatorModelLineItem.objects.filter(is_active=True).first()
        self.assertIsNotNone(item)
        labels = _spec_labels(item, 'en')
        self.assertIn('General', labels)
        # Имя группы задаётся данными (spec_template_i18n), правки переводов в
        # админке могут менять его («Technical» / «Technical specifications»).
        self.assertTrue(any(l.startswith('Technical') for l in labels))
        self.assertNotIn('Основные', labels)


class SeriesTemplateI18nTests(TestCase):
    """name_template_i18n/description_template_i18n серий."""

    def test_cg_item_generate_name_en(self):
        item = CableGland.objects.filter(is_active=True).first()
        name = item.generate_name('en')
        self.assertIn('Cable gland', name)
        self.assertNotIn('Кабельный ввод', name)

    def test_cg_item_generate_name_cn(self):
        item = CableGland.objects.filter(is_active=True).first()
        name = item.generate_name('cn')
        self.assertIn('电缆接头', name)

    def test_sv_item_generate_name_en(self):
        item = DirectionValve.objects.filter(is_active=True).first()
        name = item.generate_name('en')
        self.assertIn('Solenoid valve', name)
        self.assertNotIn('Пневмораспределитель', name)


class CatalogDetailViewLocaleTests(TestCase):
    """Detail-вью каталогов отдают локализованные секции характеристик."""

    def setUp(self):
        self.client = Client()

    def _get_spec_labels(self, url, accept_language):
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=accept_language)
        self.assertEqual(response.status_code, 200)
        for section in response.json().get('sections', []):
            if section.get('key') == 'specs':
                data = section.get('data') or {}
                return list(data.keys()) + [
                    label for fields in data.values() if isinstance(fields, dict)
                    for label in fields.keys()
                ]
        return []

    def test_cg_detail_en_vs_ru(self):
        item = CableGland.objects.filter(is_active=True).first()
        url = f'/api/cable-glands/catalog/{item.id}/'
        en_labels = self._get_spec_labels(url, 'en')
        ru_labels = self._get_spec_labels(url, 'ru')
        self.assertIn('General', en_labels)
        self.assertIn('Основные', ru_labels)

    def test_sv_detail_zh_cn(self):
        item = DirectionValve.objects.filter(is_active=True).first()
        url = f'/api/solenoid-valves/catalog/{item.id}/'
        labels = self._get_spec_labels(url, 'zh-CN')
        self.assertIn('基本参数', labels)

    def test_sv_sections_en_description(self):
        """sections/ локализует описание серии (образец БКВ)."""
        response = self.client.get(
            '/api/solenoid-valves/sections/', HTTP_ACCEPT_LANGUAGE='en'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data)
        by_name = {s['name']: s for s in data}
        self.assertIn('RP', by_name)
        self.assertIn('valve series', by_name['RP'].get('description', ''))

    def test_sv_sections_ru_default(self):
        response = self.client.get('/api/solenoid-valves/sections/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        by_name = {s['name']: s for s in data}
        self.assertIn('распределителей', by_name['RP'].get('description', ''))


class CatalogSectionsI18nTests(TestCase):
    """sections/-эндпоинты каталогов отдают локализованные описания серий."""

    def setUp(self):
        self.client = Client()

    def _sections(self, url, accept_language):
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=accept_language)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data)
        return data

    def test_gearbox_sections_en(self):
        data = self._sections('/api/gearbox/sections/', 'en')
        self.assertTrue(all(s['count'] > 0 for s in data))
        joined = ' '.join(s.get('description') or '' for s in data)
        self.assertIn('manual overrides', joined)

    def test_filter_regulator_sections_en(self):
        data = self._sections('/api/filter-regulator/sections/', 'en')
        self.assertTrue(all(s['count'] > 0 for s in data))
        joined = ' '.join(s.get('description') or '' for s in data)
        self.assertIn('Filter regulators', joined)

    def test_cable_glands_sections_en(self):
        data = self._sections('/api/cable-glands/sections/', 'en')
        self.assertTrue(all(s['count'] > 0 for s in data))
        joined = ' '.join(s.get('description') or '' for s in data)
        self.assertIn('cable gland', joined.lower())

    def test_fittings_family_sections_scoped_by_kind(self):
        fittings = self._sections('/api/pneumatic-fittings/sections/', 'en')
        silencers = self._sections('/api/pneumatic-silencers/sections/', 'en')
        plugs = self._sections('/api/pneumatic-plugs/sections/', 'en')
        for data in (fittings, silencers, plugs):
            self.assertTrue(all(s['count'] > 0 for s in data))
        f_names = {s['name'] for s in fittings}
        p_names = {s['name'] for s in plugs}
        self.assertTrue(p_names)
        self.assertNotEqual(f_names, p_names)  # виды не пересекаются полностью

    def test_pa_model_lines_en(self):
        data = self._sections('/api/pneumatic_actuators/constructor/model_lines/', 'en')
        joined = ' '.join(s.get('description') or '' for s in data)
        self.assertIn('actuator series', joined.lower())

    def test_sv_engineer_en_localized_fields(self):
        """Карточки подбора: name/title/list_title генерируются из локализованных шаблонов."""
        response = self.client.get('/api/solenoid-valves/engineer/', HTTP_ACCEPT_LANGUAGE='en')
        self.assertEqual(response.status_code, 200)
        data = response.json().get('data', [])
        self.assertTrue(data)
        first = data[0]
        self.assertIn('Solenoid valve', first.get('name') or '')
        self.assertIn('Solenoid valve', first.get('title') or '')
        self.assertNotIn('Пневмораспределитель', (first.get('title') or '') + (first.get('name') or ''))


class TranslateCommandsIdempotencyTests(TestCase):
    """Команды-переводчики не меняют уже заполненные локали (--dry-run)."""

    def test_translate_spec_templates_dry_run_no_updates(self):
        # Повторный dry-run по заполненной БД не должен ничего менять
        et = EquipmentType.objects.get(code='cable-gland')
        i18n_before = dict(et.spec_template_i18n or {})
        call_command('translate_spec_templates', '--dry-run', stdout=StringIO())
        et.refresh_from_db()
        self.assertEqual(et.spec_template_i18n, i18n_before)

    def test_translate_model_line_templates_dry_run_no_updates(self):
        ml = CableGlandModelLine.objects.first()
        before = dict(ml.name_template_i18n or {})
        call_command('translate_model_line_templates', '--dry-run', stdout=StringIO())
        ml.refresh_from_db()
        self.assertEqual(ml.name_template_i18n, before)


class TranslateCommandFillMissingTests(TestCase):
    """Команды дозаполняют только отсутствующие локали; --force перезаписывает."""

    def test_reference_dicts_keeps_manual_fix_and_force_overwrites(self):
        obj = FittingShape.objects.get(name='Прямой')
        obj.name_i18n = {'ru': obj.name, 'en': 'MANUAL-FIX', 'cn': '直通'}
        obj.save(update_fields=['name_i18n'])

        # Без --force ручная правка сохраняется
        call_command('translate_reference_dicts', stdout=StringIO())
        obj.refresh_from_db()
        self.assertEqual(obj.name_i18n.get('en'), 'MANUAL-FIX')

        # --force возвращает словарное значение
        call_command('translate_reference_dicts', '--force', stdout=StringIO())
        obj.refresh_from_db()
        self.assertEqual(obj.name_i18n.get('en'), 'Straight')


class AdminI18nFieldsetTests(TestCase):
    """Глобальный блок «Переводы (ru/en/cn)» в админке (admin_site.py)."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            'i18n-admin', 'i18n-admin@example.com', 'test-password')
        self.client.force_login(self.user)

    def test_block_and_widget_added(self):
        obj = SilencerShape.objects.first()
        response = self.client.get(
            f'/admin/pneumatic_fittings/silencershape/{obj.pk}/change/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('Переводы (ru/en/cn)', html)
        self.assertIn('i18n-json-field', html)
        self.assertIn('i18n_json_field.js', html)

    def test_no_duplicate_fields_when_admin_shows_them_already(self):
        ml = PneumaticSilencerModelLine.objects.first()
        response = self.client.get(
            f'/admin/pneumatic_fittings/pneumaticsilencermodelline/{ml.pk}/change/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertEqual(html.count('<textarea name="name_template_i18n"'), 1)
        self.assertEqual(html.count('<textarea name="description_i18n"'), 1)

    def test_equipment_type_admin_gets_all_i18n_fields_once(self):
        et = EquipmentType.objects.get(code='pneumatic-actuator')
        response = self.client.get(
            f'/admin/core/equipmenttype/{et.pk}/change/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('Переводы (ru/en/cn)', html)
        self.assertEqual(html.count('<textarea name="name_template_i18n"'), 1)


class ThroughOptionLocalizedNameTests(SimpleTestCase):
    """localized_name() через-опций: авто-суффикс (Стандарт)/(Опция) + делегирование."""

    def test_strip_option_suffix_case_insensitive(self):
        from options.exd import BaseThroughOptionNoDefault
        self.assertEqual(BaseThroughOptionNoDefault._strip_option_suffix('Handwheel (option)'), 'Handwheel')
        self.assertEqual(BaseThroughOptionNoDefault._strip_option_suffix('Не установлен (Стандарт)'), 'Не установлен')
        self.assertEqual(BaseThroughOptionNoDefault._strip_option_suffix('IP67 (Standard)'), 'IP67')

    def test_localized_name_adds_suffix_default_vs_option(self):
        from params.models import HandWheelInstalledOption
        from pneumatic_actuators.models.pa_options import PneumaticManualOverrideOption
        ref = HandWheelInstalledOption(
            name='Не установлен',
            name_i18n={'ru': 'Не установлен', 'en': 'Not installed', 'cn': '未安装'},
        )
        default = PneumaticManualOverrideOption(hand_wheel_option=ref, is_default=True)
        option = PneumaticManualOverrideOption(hand_wheel_option=ref, is_default=False)
        self.assertEqual(default.localized_name('en'), 'Not installed (Standard)')
        self.assertEqual(option.localized_name('en'), 'Not installed (Option)')
        self.assertEqual(default.localized_name('cn'), '未安装 （标配）')

    def test_no_double_suffix_for_reference_with_option_word(self):
        from params.models import HandWheelInstalledOption
        from pneumatic_actuators.models.pa_options import PneumaticManualOverrideOption
        ref = HandWheelInstalledOption(
            name='Штурвал (опция)',
            name_i18n={'ru': 'Штурвал (опция)', 'en': 'Handwheel (option)', 'cn': '手轮（选配）'},
        )
        opt = PneumaticManualOverrideOption(hand_wheel_option=ref, is_default=False)
        self.assertEqual(opt.localized_name('en'), 'Handwheel (Option)')
        self.assertEqual(opt.localized_name('cn'), '手轮 （选配）')
        self.assertNotIn('(option) (Option)', opt.localized_name('en'))

    def test_free_function_delegates_to_method(self):
        from params.models import HandWheelInstalledOption
        from pneumatic_actuators.models.pa_options import PneumaticManualOverrideOption
        from core.utils.localization import localized_name as localize
        ref = HandWheelInstalledOption(
            name='Не установлен',
            name_i18n={'ru': 'Не установлен', 'en': 'Not installed', 'cn': '未安装'},
        )
        opt = PneumaticManualOverrideOption(hand_wheel_option=ref, is_default=True)
        self.assertEqual(localize(opt, 'en'), opt.localized_name('en'))
        self.assertEqual(localize(opt, 'cn'), opt.localized_name('cn'))

    def test_safety_springs_str_have_suffix(self):
        from params.models import SafetyPositionOption
        from pneumatic_actuators.models.pa_options import (
            PneumaticSafetyPositionOption, PneumaticSpringsQtyOption)
        from pneumatic_actuators.models.pa_params import PneumaticActuatorSpringsQty
        sp = PneumaticSafetyPositionOption(
            safety_position=SafetyPositionOption(name='NC'), is_default=True)
        sq = PneumaticSpringsQtyOption(
            springs_qty=PneumaticActuatorSpringsQty(name='05'), is_default=False)
        self.assertEqual(str(sp), 'NC (Стандарт)')
        self.assertEqual(str(sq), '05 (Опция)')
        self.assertEqual(sp.localized_name('en'), 'NC (Standard)')
        self.assertEqual(sq.localized_name('en'), '05 (Option)')

