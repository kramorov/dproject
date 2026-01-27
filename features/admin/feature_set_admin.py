# features/admin/feature_set_admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from features.models.feature_set import FeatureSet
from features.models.feature_template import FeatureTemplate
import json


class FeatureSetForm(forms.ModelForm):
    class Meta:
        model = FeatureSet
        fields = '__all__'
        widgets = {
            'feature_values': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Фильтруем шаблоны
        self.fields['feature_template'].queryset = FeatureTemplate.objects.filter(is_active=True)

        # Фильтруем ContentType (только модели, которые могут иметь характеристики)
        self.fields['content_type'].queryset = ContentType.objects.filter(
            model__in=[
                'pneumaticactuatorselected',
                'controlunitinstalledoption',
                'valve',
                'actuator',
                'equipment'
            ]
        ).order_by('model')

        # Добавляем поле для поиска объекта
        if self.instance and self.instance.content_type_id:
            model_class = self.instance.content_type.model_class()
            if model_class:
                self.fields['object_search'] = forms.CharField(
                    required=False,
                    label=f"Поиск объекта {model_class._meta.verbose_name}",
                    help_text=f"Введите название или код объекта",
                    widget=forms.TextInput(attrs={
                        'class': 'object-search',
                        'placeholder': 'Начните вводить для поиска...'
                    })
                )


@admin.register(FeatureSet)
class FeatureSetAdmin(admin.ModelAdmin):
    form = FeatureSetForm
    list_display = [
        'name', 'code', 'feature_template_display',
        'related_object_display', 'completion_bar',
        'is_approved_badge', 'is_active', 'created_at'
    ]

    list_filter = ['feature_template', 'is_approved', 'is_active', 'content_type']
    search_fields = ['name', 'code', 'description']
    readonly_fields = [
        'features_editor', 'completion_stats',
        'approval_info', 'preview_table'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'description')
        }),
        ('Привязка к объекту', {
            'fields': ('feature_template', 'content_type', 'object_id', 'object_search'),
            'classes': ('wide',),
        }),
        ('Характеристики', {
            'fields': ('features_editor', 'feature_values'),
            'classes': ('wide',),
        }),
        ('Статистика', {
            'fields': ('completion_stats', 'preview_table'),
            'classes': ('collapse',),
        }),
        ('Утверждение', {
            'fields': ('is_approved', 'approved_by', 'approved_at', 'approval_info'),
            'classes': ('collapse',),
        }),
        ('Настройки', {
            'fields': ('is_active',)
        }),
    )

    actions = ['approve_feature_sets', 'duplicate_feature_sets']

    def feature_template_display(self, obj):
        """Отображение шаблона характеристик"""
        if obj.feature_template:
            url = reverse('admin:features_featuretemplate_change', args=[obj.feature_template.id])
            return format_html(
                '<a href="{}">{}</a><br><small>{}</small>',
                url, obj.feature_template.name,
                obj.feature_template.equipment_type.name
            )
        return "—"

    feature_template_display.short_description = "Шаблон"

    def related_object_display(self, obj):
        """Отображение связанного объекта"""
        related_obj = obj.get_related_object()
        if related_obj:
            # Пытаемся получить URL для редактирования
            try:
                url = reverse(
                    f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                    args=[obj.object_id]
                )
                return format_html(
                    '<a href="{}">{}</a><br><small>{}</small>',
                    url, str(related_obj),
                    obj.content_type.model_class()._meta.verbose_name
                )
            except:
                return format_html(
                    '{}<br><small>{}</small>',
                    str(related_obj),
                    obj.content_type.model_class()._meta.verbose_name
                )
        return format_html(
            '<span style="color: #dc3545;">Объект не найден</span><br>'
            '<small>ID: {}</small>',
            obj.object_id
        )

    related_object_display.short_description = "Связанный объект"

    def completion_bar(self, obj):
        """Полоса прогресса заполнения"""
        percentage = obj.get_completion_percentage()

        if percentage == 100:
            color = '#28a745'
            icon = '✅'
        elif percentage >= 70:
            color = '#17a2b8'
            icon = '🔄'
        elif percentage >= 30:
            color = '#ffc107'
            icon = '⏳'
        else:
            color = '#dc3545'
            icon = '❌'

        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<div style="flex: 1; background: #e9ecef; height: 10px; border-radius: 5px; '
            'overflow: hidden;">'
            '<div style="width: {}%; height: 100%; background: {};"></div>'
            '</div>'
            '<div style="min-width: 50px; text-align: right;">'
            '{} {}%'
            '</div>'
            '</div>',
            percentage, color, icon, percentage
        )

    completion_bar.short_description = "Заполнено"

    def is_approved_badge(self, obj):
        """Бейдж утверждения"""
        if obj.is_approved:
            return format_html(
                '<span class="badge" style="background: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 12px; font-weight: bold;">'
                '✅ Утвержден</span>'
            )
        return format_html(
            '<span class="badge" style="background: #6c757d; color: white; '
            'padding: 3px 10px; border-radius: 12px;">Черновик</span>'
        )

    is_approved_badge.short_description = "Статус"

    def features_editor(self, obj):
        """Редактор значений характеристик"""
        if not obj.pk:
            return "Сначала сохраните набор"

        if not obj.feature_template:
            return "Выберите шаблон характеристик"

        features = obj.get_feature_values_with_details()

        html = f'''
        <div id="feature-set-editor" data-feature-set-id="{obj.id}">
            <div style="margin-bottom: 20px;">
                <div style="display: flex; gap: 10px; align-items: center;">
                    <button type="button" class="button" id="save-feature-values-btn"
                            style="background: #28a745; color: white;"
                            {'disabled' if obj.is_approved else ''}>
                        💾 Сохранить все значения
                    </button>
                    <button type="button" class="button" id="reset-to-defaults-btn">
                        🔄 Сбросить к значениям по умолчанию
                    </button>
                    <span id="save-status" style="margin-left: 10px;"></span>
                </div>
                {'<div style="margin-top: 10px; padding: 10px; background: #fff3cd; '
                 'border-radius: 3px;">⚠️ Набор утвержден, редактирование запрещено</div>'
        if obj.is_approved else ''}
            </div>

            <div id="features-values-list">
        '''

        for i, item in enumerate(features, 1):
            feature = item['feature']
            value = item['value']
            is_default = item['is_default']
            is_required = item['is_required']
            template_default = item['template_default']

            # Определяем тип поля ввода
            input_field = self._get_input_field(feature, value, obj.is_approved)

            html += f'''
            <div class="feature-value-item" data-feature-id="{feature.id}" 
                 style="margin-bottom: 15px; padding: 15px; border: 1px solid #ddd; 
                        border-radius: 5px; background: #f9f9f9; 
                        {'border-left: 4px solid #dc3545;' if is_required and not value else ''}
                        {'border-left: 4px solid #28a745;' if is_default else ''}">
                <div style="display: flex; justify-content: space-between; 
                            align-items: center; margin-bottom: 10px;">
                    <div>
                        <span style="font-weight: bold;">#{i}. {feature.name}</span>
                        <span style="color: #666; margin-left: 10px;">({feature.code})</span>
                        {' <span style="color: #dc3545; font-weight: bold;">⚠️ Обязательно</span>'
            if is_required else ''}
                    </div>
                    <div>
                        <span style="color: #6c757d; font-size: 0.9em;">
                            {feature.get_data_type_display()}
                            {f" ({feature.unit})" if feature.unit else ""}
                        </span>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                            Значение:
                        </label>
                        {input_field}
                        <div style="margin-top: 5px;">
                            <button type="button" class="button use-default-btn" 
                                    style="font-size: 0.9em; padding: 2px 8px;"
                                    {'disabled' if obj.is_approved else ''}>
                                Использовать значение по умолчанию
                            </button>
                            <span class="default-value" style="display: none;">
                                {template_default}
                            </span>
                        </div>
                    </div>

                    <div>
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                            Информация:
                        </label>
                        <div style="padding: 8px; background: #f8f9fa; border-radius: 3px;">
                            <div style="margin-bottom: 5px;">
                                <strong>По умолчанию:</strong><br>
                                {template_default or '-'} {feature.unit or ''}
                            </div>
                            <div>
                                <strong>Статус:</strong><br>
                                {'✅ Используется значение по умолчанию' if is_default
            else '✏️ Измененное значение'}
                            </div>
                        </div>
                    </div>
                </div>

                {f'<div style="margin-top: 10px; color: #666; font-size: 0.9em;">'
                 f'{feature.help_text}</div>' if feature.help_text else ''}
            </div>
            '''

        html += '''
            </div>
        </div>
        '''

        return format_html(html)

    features_editor.short_description = "Редактор значений характеристик"

    def _get_input_field(self, feature, value, is_approved):
        """Получить поле ввода в зависимости от типа данных"""
        disabled = 'disabled' if is_approved else ''

        if feature.data_type == 'boolean':
            checked_true = 'checked' if str(value).lower() in ['true', '1', 'да', 'yes'] else ''
            checked_false = 'checked' if str(value).lower() in ['false', '0', 'нет', 'no'] else ''

            return f'''
            <div style="display: flex; gap: 15px;">
                <label>
                    <input type="radio" name="feature_{feature.id}" value="true" 
                           {checked_true} {disabled}>
                    Да
                </label>
                <label>
                    <input type="radio" name="feature_{feature.id}" value="false" 
                           {checked_false} {disabled}>
                    Нет
                </label>
            </div>
            '''

        elif feature.data_type == 'select':
            options = ['<option value="">-- Выберите --</option>']
            choices = feature.get_choices_list()

            for choice in choices:
                selected = 'selected' if choice == value else ''
                options.append(f'<option value="{choice}" {selected}>{choice}</option>')

            return f'''
            <select name="feature_{feature.id}" style="width: 100%; padding: 8px;" {disabled}>
                {''.join(options)}
            </select>
            '''

        elif feature.data_type == 'number':
            min_attr = f'min="{feature.min_value}"' if feature.min_value is not None else ''
            max_attr = f'max="{feature.max_value}"' if feature.max_value is not None else ''
            step_attr = 'step="any"'

            return f'''
            <input type="number" name="feature_{feature.id}" value="{value or ''}"
                   style="width: 100%; padding: 8px;" 
                   {min_attr} {max_attr} {step_attr} {disabled}>
            '''

        else:  # text, range, file, link
            rows = 3 if feature.data_type == 'text' else 1

            return f'''
            <textarea name="feature_{feature.id}" rows="{rows}"
                      style="width: 100%; padding: 8px; resize: vertical;" 
                      {disabled}>{value or ''}</textarea>
            '''

    def completion_stats(self, obj):
        """Статистика заполнения"""
        features = obj.get_feature_values_with_details()
        if not features:
            return "Нет характеристик в наборе"

        total = len(features)
        filled = sum(1 for item in features if item['value'])
        required_total = sum(1 for item in features if item['is_required'])
        required_filled = sum(1 for item in features if item['is_required'] and item['value'])
        changed = sum(1 for item in features if not item['is_default'])

        html = '''
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; 
                    margin: 15px 0;">
        '''

        stats = [
            ('Всего характеристик', total, '#007bff'),
            ('Заполнено', f'{filled}/{total}', '#28a745'),
            ('Обязательные', f'{required_filled}/{required_total}',
             '#dc3545' if required_filled < required_total else '#28a745'),
            ('Изменены', changed, '#ffc107'),
        ]

        for label, value, color in stats:
            html += f'''
            <div style="text-align: center; padding: 10px; background: {color}10; 
                        border: 1px solid {color}30; border-radius: 5px;">
                <div style="font-size: 1.5em; font-weight: bold; color: {color};">{value}</div>
                <div style="color: #666; font-size: 0.9em;">{label}</div>
            </div>
            '''

        html += '</div>'

        # Прогресс-бар
        percentage = obj.get_completion_percentage()
        html += f'''
        <div style="margin-top: 20px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Общий прогресс заполнения</span>
                <span>{percentage}%</span>
            </div>
            <div style="background: #e9ecef; height: 10px; border-radius: 5px; overflow: hidden;">
                <div style="width: {percentage}%; height: 100%; background: #28a745;"></div>
            </div>
        </div>
        '''

        return format_html(html)

    completion_stats.short_description = "Статистика заполнения"

    def preview_table(self, obj):
        """Предпросмотр таблицы характеристик"""
        return format_html(obj.get_features_table())

    preview_table.short_description = "Предпросмотр таблицы"

    def approval_info(self, obj):
        """Информация об утверждении"""
        if not obj.is_approved:
            return "Набор не утвержден"

        html = f'''
        <div style="padding: 15px; background: #d4edda; border: 1px solid #c3e6cb; 
                    border-radius: 5px;">
            <h4>✅ Набор характеристик утвержден</h4>
            <div style="margin-top: 10px;">
                <div><strong>Дата утверждения:</strong> {obj.approved_at.strftime("%d.%m.%Y %H:%M") if obj.approved_at else "Не указана"}</div>
                <div><strong>Утвердил:</strong> {obj.approved_by.get_full_name() if obj.approved_by else "Не указан"}</div>
            </div>
        </div>
        '''
        return format_html(html)

    approval_info.short_description = "Информация об утверждении"

    # Действия администратора
    def approve_feature_sets(self, request, queryset):
        """Утвердить выбранные наборы характеристик"""
        count = 0
        for feature_set in queryset.filter(is_approved=False):
            feature_set.is_approved = True
            feature_set.approved_by = request.user
            feature_set.save()
            count += 1

        self.message_user(
            request,
            f"Утверждено наборов характеристик: {count}",
            level='success'
        )

    approve_feature_sets.short_description = "✅ Утвердить выбранные наборы"

    def duplicate_feature_sets(self, request, queryset):
        """Дублировать выбранные наборы характеристик"""
        count = 0
        for original in queryset:
            # Создаем копию
            duplicate = FeatureSet.objects.create(
                name=f"{original.name} (копия)",
                code=f"{original.code}_COPY",
                description=original.description,
                feature_template=original.feature_template,
                content_type=original.content_type,
                object_id=original.object_id,
                feature_values=original.feature_values.copy(),
                is_approved=False,  # Копия не утверждена
                is_active=original.is_active,
            )
            count += 1

        self.message_user(
            request,
            f"Создано копий наборов характеристик: {count}",
            level='success'
        )

    duplicate_feature_sets.short_description = "📋 Дублировать выбранные наборы"

    class Media:
        css = {
            'all': ('features/css/admin-feature-set.css',)
        }
        js = ('features/js/admin-feature-set.js',)