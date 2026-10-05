"""
Тесты Шага 4 (Фаза 4): display_i18n на айтеме БКВ.

Данные — из копии боевой БД: прогон `python manage.py test pa_controls --keepdb`.
TestCase транзакционный — изменения откатываются, копия не портится.
"""
from django.test import TestCase, Client

from pa_controls.models import LimitSwitchBox, LimitSwitchSensorVariety


class DisplayI18nTests(TestCase):
    """display_i18n: все локали/поля, соответствие generate_*, отражение правок шаблона."""

    def _first_item(self):
        return LimitSwitchBox.objects.select_related('model_line').first()

    def test_display_i18n_has_all_locales_and_fields(self):
        item = self._first_item()
        if item is None:
            self.skipTest('В копии БД нет айтемов БКВ')
        item.save()  # полный save → display_i18n пересчитывается
        self.assertEqual(set(item.display_i18n.keys()), {'ru', 'en', 'cn'})
        for loc in ('ru', 'en', 'cn'):
            for f in ('name', 'description', 'title', 'list_title', 'spec_title'):
                self.assertIn(f, item.display_i18n[loc])

    def test_display_matches_generate(self):
        item = self._first_item()
        if item is None:
            self.skipTest('В копии БД нет айтемов БКВ')
        item.save()
        self.assertEqual(item.display_i18n['ru']['name'], item.generate_name())
        self.assertEqual(item.display_i18n['en']['name'], item.generate_name('en'))
        self.assertEqual(item.display_i18n['cn']['title'], item.generate_title('cn'))

    def test_template_change_reflected_after_resave(self):
        item = self._first_item()
        if item is None or not item.model_line or not item.model_line.name_template:
            self.skipTest('Нет model_line/шаблона')
        ml = item.model_line
        old = dict(ml.name_template_i18n or {})
        ml.name_template_i18n = dict(old)
        ml.name_template_i18n['en'] = 'TST-EN {model_code}'
        ml.save()
        item.save()
        try:
            self.assertTrue(item.display_i18n['en']['name'].startswith('TST-EN'))
            self.assertEqual(item.display_i18n['en']['name'], item.generate_name('en'))
        finally:
            ml.name_template_i18n = old
            ml.save()

    def test_skip_display_i18n_keeps_existing(self):
        item = self._first_item()
        if item is None:
            self.skipTest('В копии БД нет айтемов БКВ')
        item.save()
        saved = item.display_i18n
        item.save(skip_display_i18n=True)
        item.refresh_from_db()
        self.assertEqual(item.display_i18n, saved)


class LocaleApiTests(TestCase):
    """Шаг 5: API отдаёт локализованные данные по Accept-Language (копия БД)."""

    def setUp(self):
        self.client = Client()
        self.variety = LimitSwitchSensorVariety.objects.filter(name='Механический').first()

    def _set_variety_en(self, value='Mechanical EN'):
        if self.variety is None:
            self.skipTest('В копии нет variety «Механический»')
        self.variety.name_i18n = dict(self.variety.name_i18n or {})
        self.variety.name_i18n['en'] = value
        self.variety.save()

    def test_filters_labels_localized(self):
        en = self.client.get('/api/pa-controls/filters/', HTTP_ACCEPT_LANGUAGE='en')
        ru = self.client.get('/api/pa-controls/filters/', HTTP_ACCEPT_LANGUAGE='ru')
        self.assertEqual(en.status_code, 200)
        self.assertEqual(en.json()['filters']['sensor_variety_id']['label'], 'Sensor type')
        self.assertEqual(ru.json()['filters']['sensor_variety_id']['label'], 'Тип сенсора')

    def test_filter_option_names_localized(self):
        self._set_variety_en()
        en = self.client.get('/api/pa-controls/filters/', HTTP_ACCEPT_LANGUAGE='en')
        opts = en.json()['filters']['sensor_variety_id']['options']
        names = {o['id']: o['name'] for o in opts}
        self.assertEqual(names.get(self.variety.id), 'Mechanical EN')

    def test_detail_localized(self):
        self._set_variety_en()
        item = LimitSwitchBox.objects.filter(sensor_variety=self.variety).first()
        if item is None:
            self.skipTest('Нет айтема с variety «Механический»')
        item.save()  # пересчёт display_i18n (транзакция откатится)
        en = self.client.get(f'/api/pa-controls/catalog/{item.pk}/', HTTP_ACCEPT_LANGUAGE='en')
        ru = self.client.get(f'/api/pa-controls/catalog/{item.pk}/', HTTP_ACCEPT_LANGUAGE='ru')
        self.assertEqual(en.status_code, 200)
        self.assertIn('Mechanical EN', en.json()['name'])
        self.assertNotIn('Mechanical EN', ru.json()['name'])

    def test_list_localized(self):
        self._set_variety_en()
        item = LimitSwitchBox.objects.filter(sensor_variety=self.variety).first()
        if item is None:
            self.skipTest('Нет айтема с variety «Механический»')
        item.save()
        en = self.client.get('/api/pa-controls/catalog/', HTTP_ACCEPT_LANGUAGE='en')
        en_names = [i['name'] for i in en.json()['data']]
        self.assertTrue(any('Mechanical EN' in n for n in en_names))


class SpecDocContextLocaleTests(TestCase):
    """Шаг 6: get_spec_doc_context(locale) — заголовок и подписи спецификации локализуются."""

    def test_spec_context_localized(self):
        from core.models import EquipmentType
        item = LimitSwitchBox.objects.select_related('model_line').first()
        if item is None:
            self.skipTest('Нет айтемов в копии')
        et = item._get_equipment_type()
        if et is None:
            self.skipTest('Нет EquipmentType у БКВ')
        old_title_i18n = dict(et.spec_title_template_i18n or {})
        old_spec_i18n = dict(et.spec_template_i18n or {})
        et.spec_title_template_i18n = dict(old_title_i18n)
        et.spec_title_template_i18n['en'] = 'EN-SPEC {model_code}'
        spec = et.spec_template or {}
        if isinstance(spec, dict) and spec:
            en_spec = {}
            for g, fields in spec.items():
                if isinstance(fields, dict):
                    en_spec['EN-' + g] = {('EN-' + k): v for k, v in fields.items()}
            et.spec_template_i18n = dict(old_spec_i18n)
            et.spec_template_i18n['en'] = en_spec
        et.save()
        try:
            ctx = item.get_spec_doc_context(locale='en')
            self.assertTrue(ctx['item']['title'].startswith('EN-SPEC'))
            if isinstance(spec, dict) and spec:
                self.assertTrue(ctx['spec_groups'][0]['title'].startswith('EN-'))
                self.assertTrue(ctx['spec_groups'][0]['rows'][0]['label'].startswith('EN-'))
            ru_ctx = item.get_spec_doc_context(locale='ru')
            self.assertEqual(ru_ctx['item']['title'], item.generate_spec_title())
        finally:
            et.spec_title_template_i18n = old_title_i18n
            et.spec_template_i18n = old_spec_i18n
            et.save()
