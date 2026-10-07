"""
Тесты локализации spec_template/шаблонов серий и detail-вью каталогов.

Прогон — на копии рабочей БД (`test_db.sqlite3`, см. SESSION.md §8):
    python manage.py test core.tests.test_catalog_i18n --keepdb

Покрытие:
  - spec_template_i18n: серия КВ с собственным шаблоном, ПП-айтем через EquipmentType;
  - синхронизация ru в spec_template_i18n при save() серии;
  - name_template_i18n: generate_name('en'/'cn') реального айтема;
  - detail-вью каталогов: локаль из Accept-Language;
  - идемпотентность команд-переводчиков (--dry-run, без записи).
"""
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase

from cable_glands.models import CableGland, CableGlandModelLine
from pneumatic_actuators.models import PneumaticActuatorModelLineItem
from solenoid_valves.models import DirectionValve


def _spec_labels(item, locale):
    """Плоский список (группа, подпись) из _get_spec_sections(locale)."""
    result = []
    for group, fields in item._get_spec_sections(locale=locale).items():
        result.append(group)
        result.extend(fields.keys())
    return result


class SpecTemplateI18nTests(TestCase):
    """spec_template_i18n: серии с собственным шаблоном и EquipmentType."""

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
        self.assertIn('Technical', labels)
        self.assertNotIn('Основные', labels)

    def test_cg_series_sync_ru_on_save(self):
        ml = CableGlandModelLine.objects.first()
        original = ml.spec_template
        self.assertTrue(original)
        self.assertEqual(ml.spec_template_i18n.get('ru'), original)
        self.assertIn('en', ml.spec_template_i18n)

        # Правка ru-шаблона → save() синхронизирует ru, en остаётся
        ml.spec_template = dict(original)
        ml.spec_template.setdefault('General', {})['Body material'] = 'body_material'
        ml.save()
        ml.refresh_from_db()
        self.assertEqual(ml.spec_template_i18n['ru'], ml.spec_template)
        self.assertIn('en', ml.spec_template_i18n)


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
        item = CableGland.objects.filter(is_active=True).first()
        i18n_before = dict(getattr(item.model_line, 'spec_template_i18n') or {})
        call_command('translate_spec_templates', '--dry-run', stdout=StringIO())
        i18n_after = getattr(item.model_line, 'spec_template_i18n')
        self.assertEqual(i18n_after, i18n_before)

    def test_translate_model_line_templates_dry_run_no_updates(self):
        ml = CableGlandModelLine.objects.first()
        before = dict(ml.name_template_i18n or {})
        call_command('translate_model_line_templates', '--dry-run', stdout=StringIO())
        ml.refresh_from_db()
        self.assertEqual(ml.name_template_i18n, before)
