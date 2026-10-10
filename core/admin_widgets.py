# core/admin_widgets.py
"""Админ-виджеты для *_i18n JSON-полей переводов (ru/en/cn).

``PrettyJSONWidget`` — многострочная textarea с отступами (Django по умолчанию
выводит JSON в одну строку), кнопкой «Форматировать» и подсветкой валидности.
Подключается глобально в ``djangoProject1/admin_site.py`` для всех полей с
суффиксом ``_i18n`` (кроме вычисляемого ``display_i18n``).
"""
import json

from django import forms


class PrettyJSONWidget(forms.Textarea):
    """Textarea для JSON: отступы, моноширинность, кнопка форматирования."""

    class Media:
        css = {'all': ('admin/css/i18n_json_field.css',)}
        js = ('admin/js/i18n_json_field.js',)

    def __init__(self, attrs=None):
        default_attrs = {'class': 'i18n-json-field', 'rows': '8'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        """Красивый JSON с отступами; невалидную строку возвращаем как есть
        (подсветит JS, а форму остановит валидация JSONField)."""
        if value is None or value == '':
            return ''
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                return value
        return json.dumps(value, ensure_ascii=False, indent=2)
