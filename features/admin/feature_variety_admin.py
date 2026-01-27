# features/admin/feature_variety_admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from features.models.feature_variety import FeatureVariety
from features.models.equipment_type import EquipmentType


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
                url = reverse('admin:features_equipmenttype_change', args=[et.id])
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
        """Предпросмотр применения"""
        if not obj.pk:
            return "Сначала сохраните объект"

        html = '<div id="application-preview">'
        html += f'<h4>Эта характеристика используется в:</h4>'

        # Шаблоны характеристик
        from features.models.feature_template import FeatureTemplate
        templates = FeatureTemplate.objects.filter(
            features_data__contains=[{'type_id': obj.id}]
        )[:5]

        if templates.exists():
            html += '<p><strong>Шаблоны характеристик:</strong></p>'
            html += '<ul style="list-style-type: none; padding-left: 0;">'
            for template in templates:
                url = reverse('admin:features_featuretemplate_change', args=[template.id])
                html += f'<li style="margin: 5px 0;">'
                html += f'<a href="{url}">{template.name}</a>'
                html += f' <span style="color: #666;">({template.code})</span>'
                html += '</li>'
            html += '</ul>'
            if templates.count() > 5:
                html += f'<p><small>... и еще {templates.count() - 5} шаблонов</small></p>'
        else:
            html += '<p>Эта характеристика еще не используется в шаблонах.</p>'

        html += '</div>'
        return format_html(html)

    application_preview.short_description = "Применение характеристики"

    class Media:
        css = {
            'all': ('features/css/admin-feature-variety.css',)
        }
        js = ('features/js/admin-feature-variety.js',)