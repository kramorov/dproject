# features/models/feature_set.py
from django.db import models
from django.utils.translation import gettext_lazy as _
# Закомментировано — проект на SQLite, импорт тянет psycopg2 и ломает manage.py.
# Модель использует models.JSONField, этот импорт не нужен.
# from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from core.models import BaseAbstractModel
from .feature_template import FeatureTemplate
import json


class FeatureSet(BaseAbstractModel):
    """
    Набор характеристик для конкретного экземпляра оборудования
    """
    feature_template = models.ForeignKey(
        FeatureTemplate,
        on_delete=models.CASCADE,
        related_name='feature_sets',
        verbose_name=_("Шаблон характеристик"),
        help_text=_("Шаблон, на основе которого создается набор")
    )

    # Ссылка на объект, к которому привязан набор
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        verbose_name=_("Тип объекта"),
        help_text=_("Тип объекта, к которому привязан набор характеристик")
    )

    object_id = models.PositiveIntegerField(
        verbose_name=_("ID объекта"),
        help_text=_("ID объекта, к которому привязан набор характеристик")
    )

    # Значения характеристик в формате JSON
    feature_values = models.JSONField(
        default=dict,
        verbose_name=_("Значения характеристик"),
        help_text=_("Словарь {feature_id: value}")
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Утвержден"),
        help_text=_("Набор характеристик утвержден и не подлежит изменению")
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Дата утверждения")
    )

    approved_by = models.ForeignKey(
        'auth.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_feature_sets',
        verbose_name=_("Утвердил")
    )

    class Meta:
        verbose_name = _("Набор характеристик")
        verbose_name_plural = _("Наборы характеристик")
        ordering = ['-created_at', 'name']
        unique_together = ['content_type', 'object_id', 'feature_template']

    def clean(self):
        """Валидация перед сохранением"""
        if self.is_approved and not self.approved_by:
            raise ValidationError({
                'approved_by': 'Укажите пользователя, который утвердил набор'
            })

    def save(self, *args, **kwargs):
        """Автоматически заполняем дату утверждения"""
        if self.is_approved and not self.approved_at:
            from django.utils import timezone
            self.approved_at = timezone.now()
        elif not self.is_approved:
            self.approved_at = None
            self.approved_by = None

        super().save(*args, **kwargs)

    def get_related_object(self):
        """Получить связанный объект"""
        model = self.content_type.model_class()
        if model:
            try:
                return model.objects.get(pk=self.object_id)
            except model.DoesNotExist:
                return None
        return None

    def get_feature_values_with_details(self):
        """Получить значения характеристик с деталями"""
        from .feature_variety import FeatureVariety

        if not self.feature_template:
            return []

        # Получаем шаблон характеристик
        template_features = self.feature_template.get_features_with_details()

        result = []
        for template_item in template_features:
            feature = template_item['feature']
            feature_id = str(feature.id)

            # Получаем значение из feature_values или используем значение по умолчанию
            value = self.feature_values.get(feature_id, template_item['default_value'])

            result.append({
                'feature': feature,
                'template_default': template_item['default_value'],
                'value': value,
                'is_default': value == template_item['default_value'],
                'is_required': template_item['is_required'],
                'order': template_item['order'],
                'data_type': template_item['data_type'],
                'unit': template_item['unit'],
            })

        # Сортируем по порядку
        return sorted(result, key=lambda x: x['order'])

    def set_feature_value(self, feature_variety, value):
        """Установить значение характеристики"""
        feature_id = str(feature_variety.id)

        # Проверяем, что набор не утвержден
        if self.is_approved:
            raise ValidationError("Нельзя изменять утвержденный набор характеристик")

        # Проверяем, что характеристика есть в шаблоне
        template_features = self.feature_template.get_features_with_details()
        template_feature_ids = [str(item['feature'].id) for item in template_features]

        if feature_id not in template_feature_ids:
            raise ValidationError("Эта характеристика не входит в выбранный шаблон")

        # Валидируем значение в зависимости от типа данных
        self._validate_feature_value(feature_variety, value)

        # Сохраняем значение
        self.feature_values[feature_id] = str(value)
        self.save()

    def _validate_feature_value(self, feature_variety, value):
        """Валидация значения характеристики"""
        if feature_variety.is_required and not value:
            raise ValidationError(f"Характеристика '{feature_variety.name}' обязательна для заполнения")

        if feature_variety.data_type == 'number':
            try:
                num_value = float(value)
                if feature_variety.min_value is not None and num_value < feature_variety.min_value:
                    raise ValidationError(
                        f"Значение должно быть не меньше {feature_variety.min_value}"
                    )
                if feature_variety.max_value is not None and num_value > feature_variety.max_value:
                    raise ValidationError(
                        f"Значение должно быть не больше {feature_variety.max_value}"
                    )
            except ValueError:
                raise ValidationError(f"Некорректное числовое значение: {value}")

        elif feature_variety.data_type == 'boolean':
            if value.lower() not in ['true', 'false', '1', '0', 'да', 'нет', 'yes', 'no']:
                raise ValidationError(f"Некорректное булево значение: {value}")

        elif feature_variety.data_type == 'select':
            choices = feature_variety.get_choices_list()
            if choices and value not in choices:
                raise ValidationError(
                    f"Значение должно быть одним из: {', '.join(choices)}"
                )

        elif feature_variety.validation_regex:
            import re
            if not re.match(feature_variety.validation_regex, str(value)):
                raise ValidationError(
                    f"Значение не соответствует формату"
                )

    def get_features_table(self):
        """Получить HTML таблицу характеристик с значениями"""
        features = self.get_feature_values_with_details()
        if not features:
            return ""

        html = '''
        <table class="feature-set-table" style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <thead>
                <tr>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">№</th>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">
                        Характеристика
                    </th>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">
                        Значение
                    </th>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">
                        Статус
                    </th>
                </tr>
            </thead>
            <tbody>
        '''

        for i, item in enumerate(features, 1):
            feature = item['feature']
            value = item['value']
            is_default = item['is_default']
            is_required = item['is_required']

            # Форматируем значение
            if feature.unit and value:
                display_value = f"{value} {feature.unit}"
            else:
                display_value = value or '-'

            # Определяем цвет строки
            row_color = ''
            if is_required and not value:
                row_color = 'background: #fff3cd;'  # Предупреждение
            elif not is_default:
                row_color = 'background: #d1ecf1;'  # Измененное значение

            html += f'''
            <tr style="{row_color}">
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                    {i}
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    <strong>{feature.name}</strong><br>
                    <small style="color: #666;">
                        {feature.code} | {feature.get_data_type_display()}
                        {' ⚠️ Обязательно' if is_required else ''}
                    </small>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    {display_value}
                </td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                    {'✅' if is_default else '✏️ Изменено'}
                </td>
            </tr>
            '''

        html += '''
            </tbody>
        </table>
        '''

        return html

    def get_completion_percentage(self):
        """Процент заполнения характеристик"""
        features = self.get_feature_values_with_details()
        if not features:
            return 0

        filled = sum(1 for item in features if item['value'])
        total = len(features)

        return round((filled / total) * 100) if total > 0 else 0

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> dict:
        data = super().get_compact_data()

        # Получаем связанный объект
        related_obj = self.get_related_object()

        data.update({
            'feature_template_id': self.feature_template_id,
            'feature_template_name': self.feature_template.name,
            'content_type_id': self.content_type_id,
            'object_id': self.object_id,
            'related_object': str(related_obj) if related_obj else None,
            'is_approved': self.is_approved,
            'completion_percentage': self.get_completion_percentage(),
            'features_count': len(self.get_feature_values_with_details()),
        })
        return data

    def get_display_data(self, view_type: str = 'detail') -> dict:
        if view_type == self.LIST:
            return {
                'id': self.id,
                'name': self.name,
                'code': self.code,
                'feature_template': self.feature_template.name,
                'related_object': str(self.get_related_object()),
                'completion_percentage': self.get_completion_percentage(),
                'is_approved': self.is_approved,
                'is_active': self.is_active,
            }

        fields = self._get_base_display_fields()
        fields.update({
            'feature_template': self._format_foreign_key(
                self.feature_template,
                label=_("Шаблон характеристик"),
                icon='📋',
                priority=5,
                include_data='compact'
            ),
            'related_object': self._format_field(
                str(self.get_related_object()),
                'text',
                label=_("Связанный объект"),
                icon='🔗',
                priority=6
            ),
            'is_approved': self._format_boolean(
                self.is_approved,
                label=_("Статус утверждения"),
                true_text=_("Утвержден"),
                false_text=_("Не утвержден"),
                icon='✅',
                priority=7
            ),
            'completion_percentage': self._format_field(
                self.get_completion_percentage(),
                'number',
                label=_("Заполнено"),
                icon='📊',
                priority=8,
                unit='%'
            ),
        })

        return {
            'title': self.name,
            'subtitle': f'Шаблон: {self.feature_template.name}',
            'fields': fields,
            'actions': self._get_actions()
        }