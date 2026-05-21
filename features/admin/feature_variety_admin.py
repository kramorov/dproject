# features/admin/feature_variety_admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from features.models.feature_variety import FeatureVariety
from core.models.equipment_type import EquipmentType


class FeatureVarietyForm(forms.ModelForm):
    class Meta:
        model = FeatureVariety
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'help_text': forms.Textarea(attrs={'rows': 2}),
            'choices': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем типы оборудования по активности
        self.fields['equipment_types'].queryset = EquipmentType.objects.filter(is_active=True)

        # Добавляем класс для динамического изменения полей
        self.fields['data_type'].widget.attrs.update({
            'onchange': 'updateFieldsVisibility()',
            'class': 'data-type-select'
        })


@admin.register(FeatureVariety)
class FeatureVarietyAdmin(admin.ModelAdmin):
    form = FeatureVarietyForm
    list_display = [
        'name', 'code', 'data_type_display',
        'unit', 'is_required_badge', 'equipment_types_preview',
        'is_active', 'sorting_order'
    ]

    list_filter = ['data_type', 'is_required', 'is_active', 'equipment_types']
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ['equipment_types']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'description')
        }),
        ('Тип данных и настройки', {
            'fields': ('data_type', 'unit', 'is_required', 'default_value', 'help_text'),
            'classes': ('wide',),
        }),
        ('Дополнительные параметры (зависят от типа данных)', {
            'fields': ('choices_container', 'range_container', 'validation_container'),
            'classes': ('collapse', 'additional-fields'),
        }),
        ('Применение', {
            'fields': ('equipment_types', 'application_preview'),
            'classes': ('wide',),
        }),
        ('Настройки', {
            'fields': ('sorting_order', 'is_active')
        }),
    )

    readonly_fields = ['choices_container', 'range_container', 'validation_container', 'application_preview']

    def data_type_display(self, obj):
        """Отображение типа данных с иконкой"""
        icons = {
            'text': '📝',
            'number': '🔢',
            'boolean': '✅',
            'select': '📋',
            'range': '📊',
            'file': '📎',
            'link': '🔗',
        }
        icon = icons.get(obj.data_type, '❓')
        return f"{icon} {obj.get_data_type_display()}"

    data_type_display.short_description = "Тип данных"

    def is_required_badge(self, obj):
        """Бейдж обязательности"""
        if obj.is_required:
            return format_html(
                '<span class="badge" style="background: #dc3545; color: white; '
                'padding: 2px 8px; border-radius: 10px;">Обязательно</span>'
            )
        return format_html(
            '<span class="badge" style="background: #6c757d; color: white; '
            'padding: 2px 8px; border-radius: 10px;">Необязательно</span>'
        )

    is_required_badge.short_description = "Обязательно"

    def equipment_types_preview(self, obj):
        """Предпросмотр типов оборудования"""
        types = obj.equipment_types.all()[:3]
        if types.exists():
            items = []
            for et in types:
                url = reverse('admin:core_equipmenttype_change', args=[et.id])
                items.append(f'<a href="{url}" title="{et.name}">{et.name[:15]}</a>')

            result = ", ".join(items)
            if obj.equipment_types.count() > 3:
                result += f" ... (+{obj.equipment_types.count() - 3})"
            return format_html(result)
        return "—"

    equipment_types_preview.short_description = "Типы оборудования"

    def choices_container(self, obj):
        """Контейнер для вариантов выбора"""
        html = '''
        <div id="choices-container" class="data-type-field" style="display: none;">
            <h4>Варианты выбора</h4>
            <p>Укажите варианты выбора, каждый с новой строки:</p>
            <textarea id="id_choices" name="choices" rows="4" cols="40"
                      style="width: 100%; font-family: monospace;">{}</textarea>
            <p><small>Пример:<br>Вариант 1<br>Вариант 2<br>Вариант 3</small></p>
        </div>
        '''.format(obj.choices if obj else '')
        return format_html(html)

    choices_container.short_description = "Варианты выбора"

    def range_container(self, obj):
        """Контейнер для диапазона значений"""
        html = '''
        <div id="range-container" class="data-type-field" style="display: none;">
            <h4>Диапазон значений</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <label for="id_min_value">Минимальное значение:</label>
                    <input type="number" id="id_min_value" name="min_value" 
                           value="{}" step="any" style="width: 100%;">
                </div>
                <div>
                    <label for="id_max_value">Максимальное значение:</label>
                    <input type="number" id="id_max_value" name="max_value" 
                           value="{}" step="any" style="width: 100%;">
                </div>
            </div>
        </div>
        '''.format(obj.min_value if obj and obj.min_value else '',
                   obj.max_value if obj and obj.max_value else '')
        return format_html(html)

    range_container.short_description = "Диапазон значений"

    def validation_container(self, obj):
        """Контейнер для валидации"""
        html = '''
        <div id="validation-container" class="data-type-field" style="display: none;">
            <h4>Валидация</h4>
            <label for="id_validation_regex">Регулярное выражение:</label>
            <input type="text" id="id_validation_regex" name="validation_regex" 
                   value="{}" style="width: 100%; font-family: monospace;">
            <p><small>Примеры: ^[A-Za-z]+$ (только буквы), ^d+$ (только цифры)</small></p>
        </div>
        '''.format(obj.validation_regex if obj else '')
        return format_html(html)

    validation_container.short_description = "Валидация"

    def application_preview(self, obj):
        """Предпросмотр применения характеристики в шаблонах"""
        if not obj.pk:
            return "Сначала сохраните объект"

        html = '<div id="application-preview">'
        html += f'<h4 style="margin-top: 0; color: #2c3e50;">📋 Эта характеристика используется в шаблонах:</h4>'

        from features.models.feature_template import FeatureTemplate

        # Получаем все шаблоны
        all_templates = FeatureTemplate.objects.select_related('equipment_type').filter(is_active=True)

        templates_with_feature = []

        # Фильтруем в Python, а не в БД
        for template in all_templates:
            if template.features_data:
                for feature in template.features_data:
                    if isinstance(feature, dict) and feature.get('type_id') == obj.id:
                        templates_with_feature.append(template)
                        break

        if templates_with_feature:
            html += '<table style="width: 100%; border-collapse: collapse; margin: 15px 0;">'
            html += '''
                <thead>
                    <tr>
                        <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa; text-align: left;">
                            Шаблон
                        </th>
                        <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa; text-align: left;">
                            Тип оборудования
                        </th>
                        <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa; text-align: center;">
                            По умолчанию
                        </th>
                        <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa; text-align: center;">
                            Всего хар-к
                        </th>
                    </tr>
                </thead>
                <tbody>
            '''

            for template in templates_with_feature:
                url = reverse('admin:features_featuretemplate_change', args=[template.id])

                # Находим значение по умолчанию для этой характеристики в шаблоне
                default_value = ''
                for feature in template.features_data:
                    if isinstance(feature, dict) and feature.get('type_id') == obj.id:
                        default_value = feature.get('default_value', '')
                        break

                html += f'''
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        <a href="{url}" style="text-decoration: none; font-weight: 600;">{template.name}</a>
                        <br><small style="color: #666;">{template.code}</small>
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        {template.equipment_type.name}
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                        {'✅' if template.is_default else '—'}
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                        {template.get_features_count()}
                    </td>
                </tr>
                '''

                # Добавляем информацию о значении по умолчанию
                if default_value:
                    html += f'''
                    <tr>
                        <td colspan="4" style="padding: 5px 8px 15px 25px; border: 1px solid #ddd; color: #666; font-style: italic;">
                            ⚙️ Значение по умолчанию: <strong>{default_value}</strong>
                        </td>
                    </tr>
                    '''

            html += '''
                </tbody>
            </table>
            '''

            if len(templates_with_feature) > 5:
                html += f'<p style="color: #666; margin-top: 10px;">' \
                        f'<small>Показано 5 из {len(templates_with_feature)} шаблонов</small></p>'

        else:
            html += '<div style="padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;">'
            html += '<p style="margin: 0; color: #6c757d;">📭 Эта характеристика еще не используется ни в одном шаблоне.</p>'
            html += '</div>'

        html += '</div>'

        # Добавляем кнопку для быстрого создания шаблона
        if not templates_with_feature:
            create_url = reverse('admin:features_featuretemplate_add')
            html += f'''
            <div style="margin-top: 20px;">
                <a href="{create_url}" class="button" style="background: #28a745; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px;">
                    ➕ Создать шаблон с этой характеристикой
                </a>
            </div>
            '''

        return format_html(html)

    application_preview.short_description = "Применение характеристики"

    class Media:
        css = {
            'all': ('features/css/admin-feature-variety.css',)
        }
        js = ('features/js/admin-feature-variety.js',)