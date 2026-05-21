# features/admin/feature_template_admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from django.core.exceptions import ValidationError
from features.models.feature_template import FeatureTemplate
from core.models.equipment_type import EquipmentType
from features.models.feature_variety import FeatureVariety


class FeatureTemplateForm(forms.ModelForm):
    class Meta:
        model = FeatureTemplate
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем типы оборудования
        self.fields['equipment_type'].queryset = EquipmentType.objects.filter(is_active=True)

        # Добавляем поле для выбора характеристик
        self.fields['available_features'] = forms.ModelMultipleChoiceField(
            queryset=FeatureVariety.objects.filter(is_active=True),
            required=False,
            label="Доступные характеристики",
            help_text="Выберите характеристики для добавления в шаблон"
        )


@admin.register(FeatureTemplate)
class FeatureTemplateAdmin(admin.ModelAdmin):
    form = FeatureTemplateForm
    list_display = [
        'name', 'code', 'equipment_type_display',
        'features_count_badge', 'is_default_badge',
        'is_active', 'sorting_order'
    ]

    list_filter = ['equipment_type', 'is_default', 'is_active']
    search_fields = ['name', 'code', 'description']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'description')
        }),
        ('Тип оборудования', {
            'fields': ('equipment_type', 'is_default')
        }),
        ('Характеристики', {
            'fields': ('available_features', 'features_editor', 'features_data'),
            'classes': ('wide',),
        }),
        ('Настройки', {
            'fields': ('sorting_order', 'is_active')
        }),
    )

    readonly_fields = ['features_editor']

    def equipment_type_display(self, obj):
        """Отображение типа оборудования"""
        if obj.equipment_type:
            url = reverse('admin:core_equipmenttype_change', args=[obj.equipment_type.id])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.equipment_type.name
            )
        return "—"

    equipment_type_display.short_description = "Тип оборудования"

    def features_count_badge(self, obj):
        """Бейдж количества характеристик"""
        count = obj.get_features_count()
        if count > 0:
            color = 'green' if count >= 5 else 'orange' if count >= 2 else 'gray'
            return format_html(
                '<span class="badge" style="background: {}; color: white; '
                'padding: 2px 8px; border-radius: 10px;">{} хар-к</span>',
                color, count
            )
        return format_html(
            '<span class="badge" style="background: #dc3545; color: white; '
            'padding: 2px 8px; border-radius: 10px;">нет хар-к</span>'
        )

    features_count_badge.short_description = "Характеристики"

    def is_default_badge(self, obj):
        """Бейдж шаблона по умолчанию"""
        if obj.is_default:
            return format_html(
                '<span class="badge" style="background: #007bff; color: white; '
                'padding: 2px 8px; border-radius: 10px; font-weight: bold;">'
                '⚡ По умолчанию</span>'
            )
        return "—"

    is_default_badge.short_description = "По умолчанию"

    def features_editor(self, obj):
        """Редактор характеристик"""
        if not obj.pk:
            return "Сначала сохраните шаблон"

        # Получаем доступные характеристики для этого типа оборудования
        equipment_type_id = obj.equipment_type_id
        available_features = FeatureVariety.objects.filter(
            is_active=True,
            equipment_types=equipment_type_id
        ).order_by('sorting_order', 'name')

        # Получаем текущие характеристики
        current_features = obj.get_features_with_details()

        html = f'''
        <div id="feature-template-editor" data-template-id="{obj.id}">
            <div style="margin-bottom: 20px;">
                <div style="display: flex; gap: 10px; align-items: center;">
                    <select id="feature-select" style="flex: 1; padding: 5px;">
                        <option value="">-- Выберите характеристику --</option>
        '''

        for feature in available_features:
            if feature.id not in [f['feature'].id for f in current_features]:
                html += f'''
                <option value="{feature.id}" 
                        data-name="{feature.name}"
                        data-code="{feature.code}"
                        data-data-type="{feature.data_type}"
                        data-unit="{feature.unit or ''}"
                        data-is-required="{str(feature.is_required).lower()}">
                    {feature.name} ({feature.code}) - {feature.get_data_type_display()}
                </option>
                '''

        html += '''
                    </select>
                    <button type="button" class="button" id="add-feature-btn">
                        ➕ Добавить
                    </button>
                    <button type="button" class="button" id="save-features-btn" 
                            style="background: #28a745; color: white;">
                        💾 Сохранить все изменения
                    </button>
                </div>
                <div id="add-feature-status" style="margin-top: 10px; display: none;"></div>
            </div>

            <div id="features-list-container">
        '''

        if current_features:
            html += '<h4>Текущие характеристики:</h4>'
            html += '<div id="features-list">'

            for i, item in enumerate(current_features, 1):
                feature = item['feature']
                html += f'''
                <div class="feature-item" data-feature-id="{feature.id}" 
                     style="margin-bottom: 15px; padding: 15px; border: 1px solid #ddd; 
                            border-radius: 5px; background: #f9f9f9;">
                    <div style="display: flex; justify-content: space-between; 
                                align-items: center; margin-bottom: 10px;">
                        <div>
                            <span style="font-weight: bold;">#{i}. {feature.name}</span>
                            <span style="color: #666; margin-left: 10px;">({feature.code})</span>
                        </div>
                        <div>
                            <button type="button" class="button remove-feature-btn" 
                                    style="background: #dc3545; color: white;">
                                ❌ Удалить
                            </button>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <label style="display: block; margin-bottom: 5px;">
                                <strong>Тип данных:</strong> {feature.get_data_type_display()}
                            </label>
                            <label style="display: block; margin-bottom: 5px;">
                                <strong>Единица измерения:</strong> {feature.unit or '-'}
                            </label>
                            <label style="display: block; margin-bottom: 5px;">
                                <strong>Обязательно:</strong> {'Да' if item['is_required'] else 'Нет'}
                            </label>
                        </div>

                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                                Значение по умолчанию:
                            </label>
                            <textarea class="feature-default-value" 
                                      rows="3"
                                      style="width: 100%; padding: 8px; border: 1px solid #ccc; 
                                             border-radius: 3px;">{item['default_value']}</textarea>

                            <div style="margin-top: 10px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                                    Порядок:
                                </label>
                                <input type="number" class="feature-order" 
                                       value="{item['order']}"
                                       style="width: 80px; padding: 5px; border: 1px solid #ccc; 
                                              border-radius: 3px;">
                            </div>
                        </div>
                    </div>
                </div>
                '''

            html += '</div>'
        else:
            html += '''
            <div style="padding: 20px; text-align: center; background: #f8f9fa; 
                        border: 2px dashed #dee2e6; border-radius: 5px;">
                <p style="color: #6c757d;">Нет характеристик в шаблоне</p>
                <p><small>Выберите характеристики из списка выше и нажмите "Добавить"</small></p>
            </div>
            '''

        html += '''
            </div>

            <div id="save-status" style="margin-top: 15px; padding: 10px; display: none;"></div>
        </div>
        '''

        return format_html(html)

    features_editor.short_description = "Редактор характеристик"

    class Media:
        css = {
            'all': ('features/css/admin-feature-template.css',)
        }
        js = ('features/js/admin-feature-template.js',)