"""
Тесты локализации генерации строк (Фаза 4, Шаг 1).

TemplateMixin.generate_*(locale) — локализованные шаблоны и значения справочников.
Тесты без БД (SimpleTestCase) на фейковых объектах; прогон — `manage.py test
core.tests.test_localization --keepdb`.
"""
from django.test import SimpleTestCase

from core.models.mixins import LocalizedDictFieldsMixin, TemplateMixin
from core.utils.localization import (DEFAULT_LOCALE, LOCALES,
                                     locale_from_accept_language, pick_i18n)


class _FakeBody:
    def __init__(self, name='Корпус стальной', name_i18n=None):
        self.name = name
        self.name_i18n = name_i18n or {}


class _FakeModelLine:
    def __init__(self, name_template='', name_template_i18n=None):
        self.name_template = name_template
        self.name_template_i18n = name_template_i18n or {}


class _FakeItem(TemplateMixin):
    code = 'T-1'

    def __init__(self, model_line=None, body=None):
        self.model_line = model_line
        self.body = body
        self.equipment_type_id = None

    def _get_name_template_source(self):
        if self.model_line and self.model_line.name_template:
            return self.model_line.name_template
        return None

    def _get_description_template_source(self):
        return None

    def _get_title_template_source(self):
        return None

    def _get_data_dict(self, locale=None):
        return {
            '{model_code}': 'code',
            '{body}': 'body__name',
        }


class TemplateMixinLocalizationTests(SimpleTestCase):
    """Фаза 4, Шаг 1: generate_*(locale) — локализованные шаблоны и справочники."""

    def _make_item(self, name_template='БКВ {model_code}, {body}',
                   name_template_i18n=None, body_i18n=None):
        ml = _FakeModelLine(name_template, name_template_i18n)
        return _FakeItem(model_line=ml, body=_FakeBody(name_i18n=body_i18n))

    def test_ru_default_unchanged(self):
        item = self._make_item(
            'БКВ {model_code}, {body}',
            {'en': 'LSB {model_code}, {body}'},
            {'en': 'Steel body'},
        )
        self.assertEqual(item.generate_name(), 'БКВ T-1, Корпус стальной')

    def test_en_template_and_dict_translated(self):
        item = self._make_item(
            'БКВ {model_code}, {body}',
            {'en': 'LSB {model_code}, {body}'},
            {'en': 'Steel body'},
        )
        self.assertEqual(item.generate_name('en'), 'LSB T-1, Steel body')

    def test_fallback_to_ru_when_no_translations(self):
        item = self._make_item('БКВ {model_code}, {body}')
        self.assertEqual(item.generate_name('en'), item.generate_name())
        self.assertEqual(item.generate_name('cn'), item.generate_name())

    def test_partial_translation_falls_back_to_ru_value(self):
        # перевод шаблона есть, перевода справочника нет → значение справочника на ru
        item = self._make_item(
            'БКВ {model_code}, {body}',
            {'en': 'LSB {model_code}, {body}'},
            None,
        )
        self.assertEqual(item.generate_name('en'), 'LSB T-1, Корпус стальной')

    def test_empty_i18n_dict_keeps_ru_value(self):
        # пустой _i18n (JSONField default=dict) не должен ломать ru-значение
        item = self._make_item('БКВ {model_code}, {body}', {}, {})
        self.assertEqual(item.generate_name('en'), 'БКВ T-1, Корпус стальной')

    def test_equipment_type_source_localized(self):
        class FakeET:
            description_template = '{model_code} DESCR'
            description_template_i18n = {'en': '{model_code} descr'}
            title_template = 'TITLE {model_code}'
            title_template_i18n = {'en': 'Title {model_code}'}
            spec_title_template = ''
            list_title_template = ''

        item = _FakeItem(model_line=_FakeModelLine(), body=None)
        item.equipment_type_id = 1
        item.equipment_type = FakeET()
        self.assertEqual(item.generate_description(), 'T-1 DESCR')
        self.assertEqual(item.generate_description('en'), 'T-1 descr')
        self.assertEqual(item.generate_title('en'), 'Title T-1')
        # spec_title: ET-шаблон пуст → фолбэк на title-цепочку (ET.title)
        self.assertEqual(item.generate_spec_title('en'), 'Title T-1')

    def test_translation_ignored_when_source_differs_from_model_line(self):
        """RU-шаблон из источника, отличного от model_line.<field> — перевод model_line
        применяться не должен (иначе перевод «разъедется» с шаблоном)."""
        class CustomSourceItem(_FakeItem):
            def _get_name_template_source(self):
                return 'CUSTOM {model_code}'

        ml = _FakeModelLine('ML {model_code}', {'en': 'ML EN {model_code}'})
        item = CustomSourceItem(model_line=ml, body=None)
        self.assertEqual(item.generate_name(), 'CUSTOM T-1')
        self.assertEqual(item.generate_name('en'), 'CUSTOM T-1')


class LocalizationHelpersTests(SimpleTestCase):
    """Фаза 4, Шаг 0-1: хелперы локализации (маппинг Accept-Language, pick_i18n)."""

    def test_accept_language_mapping(self):
        self.assertEqual(locale_from_accept_language('zh-CN'), 'cn')
        self.assertEqual(locale_from_accept_language('zh'), 'cn')
        self.assertEqual(locale_from_accept_language('zh-Hans'), 'cn')
        self.assertEqual(locale_from_accept_language('en-US'), 'en')
        self.assertEqual(locale_from_accept_language('ru-RU'), 'ru')
        self.assertEqual(locale_from_accept_language(None), 'ru')
        self.assertEqual(locale_from_accept_language(''), 'ru')

    def test_pick_i18n_value_fallback(self):
        # fallback-значение возвращается при отсутствии перевода
        self.assertEqual(pick_i18n({'en': 'valve'}, 'cn', fallback='клапан'), 'клапан')
        self.assertEqual(pick_i18n(None, 'en', fallback='клапан'), 'клапан')
        self.assertEqual(pick_i18n({}, 'en', fallback='клапан'), 'клапан')
        # перевод есть — он и возвращается
        self.assertEqual(pick_i18n({'en': 'valve'}, 'en', fallback='клапан'), 'valve')
        # дефолтный fallback ('ru') — прежнее поведение (locale → ru → '')
        self.assertEqual(pick_i18n({'ru': 'клапан'}, 'en'), 'клапан')
        self.assertEqual(pick_i18n({}, 'en'), '')
        self.assertEqual(LOCALES, ('ru', 'en', 'cn'))
        self.assertEqual(DEFAULT_LOCALE, 'ru')


class FakeLocalizedDict(LocalizedDictFieldsMixin):
    class Meta:
        app_label = 'core'  # конкретная модель только для теста _sync_localized_ru (без БД)


class LocalizedDictFieldsMixinTests(SimpleTestCase):
    """Фаза 4, Шаг 3: _sync_localized_ru — ru синхронизируется, переводы не затираются."""

    def test_sync_ru_preserves_translations(self):
        obj = FakeLocalizedDict()
        obj.name = 'Клапан'
        obj.name_i18n = {'en': 'Valve', 'cn': '阀'}
        obj.description = ''
        obj.description_i18n = None
        obj._sync_localized_ru()
        self.assertEqual(obj.name_i18n, {'en': 'Valve', 'cn': '阀', 'ru': 'Клапан'})
        self.assertEqual(obj.description_i18n, {'ru': ''})

    def test_sync_ru_updates_existing(self):
        obj = FakeLocalizedDict()
        obj.name = 'Новое имя'
        obj.name_i18n = {'ru': 'Старое', 'en': 'New'}
        obj.description = 'D'
        obj.description_i18n = {}
        obj._sync_localized_ru()
        self.assertEqual(obj.name_i18n['ru'], 'Новое имя')
        self.assertEqual(obj.name_i18n['en'], 'New')
        self.assertEqual(obj.description_i18n, {'ru': 'D'})
