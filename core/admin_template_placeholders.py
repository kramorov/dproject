# core/admin_template_placeholders.py
"""
TemplatePlaceholdersAdminMixin — справочник плейсхолдеров для админок model_line.

Для каждой модели-серии, где есть поля name_template/description_template,
показывает состав плейсхолдеров из _get_data_dict() соответствующей
модели-артикула каталога. Клик по плейсхолдеру вставляет его в текущее
(последнее сфокусированное) поле шаблона; кнопка «Скопировать все» кладёт
весь список в буфер обмена.

Использование:

    from core.admin_template_placeholders import TemplatePlaceholdersAdminMixin
    from my_app.models import MyItem

    @admin.register(MyModelLine)
    class MyModelLineAdmin(TemplatePlaceholdersAdminMixin, admin.ModelAdmin):
        template_item_model = MyItem
        ...
"""

from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.html import escape


class TemplatePlaceholdersAdminMixin:
    """Добавляет readonly-поле «Справочник плейсхолдеров» в форму model_line."""

    # Класс item-модели каталога (источник _get_data_dict())
    template_item_model = None
    # Заголовок fieldset'а, В КОТОРЫЙ встроить блок (иначе — отдельным в конце)
    template_placeholders_fieldset = None

    class Media:
        js = ('admin/js/template_placeholders.js',)
        css = {'all': ('admin/css/template_placeholders.css',)}

    def _get_placeholder_list(self):
        """Список плейсхолдеров {ключ} из _get_data_dict() item-модели."""
        if not self.template_item_model:
            return []
        try:
            data_dict = self.template_item_model()._get_data_dict()
        except Exception:
            return []
        if not isinstance(data_dict, dict):
            return []
        return sorted(
            k for k in data_dict.keys()
            if isinstance(k, str) and k.startswith('{') and k.endswith('}')
        )

    def template_placeholders(self, obj):
        placeholders = self._get_placeholder_list()
        if not placeholders:
            return mark_safe(
                '<div class="template-placeholders-help">'
                '<div class="tp-hint">Не задан <code>template_item_model</code> '
                'или пустой <code>_get_data_dict()</code>.</div></div>'
            )
        chips = ''.join(
            f'<span class="tp-chip" data-ph="{escape(ph)}">{escape(ph)}</span>'
            for ph in placeholders
        )
        list_text = escape(' '.join(placeholders))
        return mark_safe(
            '<div class="template-placeholders-help">'
            '<div class="tp-toolbar">'
            '<strong>Плейсхолдеры шаблонов:</strong> '
            '<button type="button" class="tp-copy-all" '
            f'data-list="{list_text}">Скопировать все</button>'
            '</div>'
            f'<div class="tp-chips">{chips}</div>'
            '<div class="tp-hint">Клик по плейсхолдеру вставляет его в '
            'последнее выбранное поле шаблона (Название/Описание). '
            'Состав определяется функцией <code>_get_data_dict()</code> '
            'модели-артикула: не хватает характеристики — добавьте её в словарь.</div>'
            '</div>'
        )
    template_placeholders.short_description = _('Справочник плейсхолдеров')

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        target = self.template_placeholders_fieldset
        if target:
            for i, (title, opts) in enumerate(fieldsets):
                if title == target:
                    fields = list(opts.get('fields', []))
                    if 'template_placeholders' not in fields:
                        fields.append('template_placeholders')
                    fieldsets[i] = (title, dict(opts, fields=fields))
                    break
            else:
                fieldsets.append((_('Справочник плейсхолдеров'), {'fields': ('template_placeholders',)}))
        else:
            fieldsets.append((_('Справочник плейсхолдеров'), {'fields': ('template_placeholders',)}))
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if 'template_placeholders' not in readonly:
            readonly.append('template_placeholders')
        return readonly
