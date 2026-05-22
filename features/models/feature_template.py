# features/models/feature_template.py
from django.db import models
from django.utils.translation import gettext_lazy as _
# Закомментировано — проект на SQLite, импорт тянет psycopg2 и ломает manage.py.
# Модель использует models.JSONField, этот импорт не нужен.
# from django.contrib.postgres.fields import JSONField
from core.models import BaseAbstractModel
from core.models.equipment_type import EquipmentType
from .feature_variety import FeatureVariety
import json


class FeatureTemplate(BaseAbstractModel):
    """
    Шаблон характеристик для типа оборудования
    """
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.CASCADE,
        related_name='feature_templates',
        verbose_name=_("Тип оборудования"),
        help_text=_("Тип оборудования, для которого создается шаблон")
    )

    # Данные характеристик в формате JSON
    features_data = models.JSONField(
        default=list,
        verbose_name=_("Характеристики шаблона"),
        help_text=_("Список характеристик: [{'type_id': X, 'default_value': '...', 'order': X}]")
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Шаблон по умолчанию"),
        help_text=_("Использовать этот шаблон по умолчанию для данного типа оборудования")
    )

    class Meta:
        verbose_name = _("Шаблон характеристик")
        verbose_name_plural = _("Шаблоны характеристик")
        ordering = ['equipment_type', 'is_default', 'sorting_order', 'name']
        unique_together = ['equipment_type', 'is_default']

    def clean(self):
        """Валидация перед сохранением"""
        from django.core.exceptions import ValidationError

        # Проверяем уникальность шаблона по умолчанию
        if self.is_default:
            existing_default = FeatureTemplate.objects.filter(
                equipment_type=self.equipment_type,
                is_default=True
            ).exclude(pk=self.pk if self.pk else None)

            if existing_default.exists():
                raise ValidationError({
                    'is_default': 'Для этого типа оборудования уже есть шаблон по умолчанию'
                })

    def add_feature(self, feature_variety, default_value="", order=0):
        """Добавить характеристику в шаблон"""
        if not self.features_data:
            self.features_data = []

        self.features_data.append({
            'type_id': feature_variety.id,
            'type_name': feature_variety.name,
            'type_code': feature_variety.code,
            'default_value': str(default_value),
            'order': order,
            'is_required': feature_variety.is_required,
            'data_type': feature_variety.data_type,
            'unit': feature_variety.unit,
        })
        self.save()

    def remove_feature(self, feature_variety_id):
        """Удалить характеристику из шаблона"""
        if self.features_data:
            self.features_data = [
                f for f in self.features_data
                if f['type_id'] != feature_variety_id
            ]
            self.save()

    def update_feature(self, feature_variety_id, default_value=None, order=None):
        """Обновить характеристику в шаблоне"""
        if self.features_data:
            for feature in self.features_data:
                if feature['type_id'] == feature_variety_id:
                    if default_value is not None:
                        feature['default_value'] = str(default_value)
                    if order is not None:
                        feature['order'] = order
                    break
            self.save()

    def get_features_with_details(self):
        """Получить характеристики с деталями"""
        if not self.features_data:
            return []

        # Получаем все виды характеристик одним запросом
        type_ids = [item['type_id'] for item in self.features_data]
        features = FeatureVariety.objects.filter(id__in=type_ids)
        feature_dict = {f.id: f for f in features}

        result = []
        for item in sorted(self.features_data, key=lambda x: x.get('order', 0)):
            feature = feature_dict.get(item['type_id'])
            if feature:
                result.append({
                    'feature': feature,
                    'default_value': item.get('default_value', ''),
                    'order': item.get('order', 0),
                    'is_required': item.get('is_required', False),
                    'data_type': item.get('data_type', 'text'),
                    'unit': item.get('unit', ''),
                })

        return result

    def get_features_table(self):
        """Получить HTML таблицу характеристик"""
        features = self.get_features_with_details()
        if not features:
            return ""

        html = '''
        <table class="features-table" style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <thead>
                <tr>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">№</th>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">
                        Характеристика
                    </th>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">
                        Тип данных
                    </th>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">
                        Значение по умолчанию
                    </th>
                    <th style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;">
                        Обязательно
                    </th>
                </tr>
            </thead>
            <tbody>
        '''

        for i, item in enumerate(features, 1):
            feature = item['feature']
            default_value = item['default_value']

            if feature.unit and default_value:
                default_value = f"{default_value} {feature.unit}"

            html += f'''
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                    {i}
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    {feature.name}<br>
                    <small style="color: #666;">{feature.code}</small>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    {feature.get_data_type_display()}
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    {default_value or '-'}
                </td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                    {'✅' if item['is_required'] else '➖'}
                </td>
            </tr>
            '''

        html += '''
            </tbody>
        </table>
        '''

        return html

    def get_features_count(self):
        """Количество характеристик в шаблоне"""
        return len(self.features_data) if self.features_data else 0

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> dict:
        data = super().get_compact_data()
        data.update({
            'equipment_type_id': self.equipment_type_id,
            'equipment_type_name': self.equipment_type.name,
            'is_default': self.is_default,
            'features_count': self.get_features_count(),
        })
        return data

    def get_display_data(self, view_type: str = 'detail') -> dict:
        if view_type == self.LIST:
            return {
                'id': self.id,
                'name': self.name,
                'code': self.code,
                'equipment_type': self.equipment_type.name,
                'features_count': self.get_features_count(),
                'is_default': self.is_default,
                'is_active': self.is_active,
            }

        fields = self._get_base_display_fields()
        fields.update({
            'equipment_type': self._format_foreign_key(
                self.equipment_type,
                label=_("Тип оборудования"),
                icon='⚙️',
                priority=5,
                include_data='compact'
            ),
            'is_default': self._format_boolean(
                self.is_default,
                label=_("Шаблон по умолчанию"),
                true_text=_("Да, шаблон по умолчанию"),
                false_text=_("Нет, дополнительный шаблон"),
                icon='🏷️',
                priority=6
            ),
            'features_count': self._format_field(
                self.get_features_count(),
                'number',
                label=_("Количество характеристик"),
                icon='📊',
                priority=7
            ),
        })

        return {
            'title': self.name,
            'subtitle': f'Для: {self.equipment_type.name}',
            'fields': fields,
            'actions': self._get_actions()
        }