# features/models/feature_variety.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseAbstractModel
from .equipment_type import EquipmentType


class FeatureVariety(BaseAbstractModel):
    """
    Вид/тип характеристики (справочник)
    """
    DATA_TYPE_CHOICES = [
        ('text', _('Текст')),
        ('number', _('Число')),
        ('boolean', _('Да/Нет')),
        ('select', _('Выбор из списка')),
        ('range', _('Диапазон')),
        ('file', _('Файл')),
        ('link', _('Ссылка')),
    ]

    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        default='text',
        verbose_name=_("Тип данных")
    )

    # Связь с типом оборудования
    equipment_types = models.ManyToManyField(
        EquipmentType,
        blank=True,
        related_name='feature_varieties',
        verbose_name=_("Типы оборудования"),
        help_text=_("Типы оборудования, для которых применяется эта характеристика")
    )

    # Для типа 'select' храним варианты выбора
    choices = models.TextField(
        blank=True,
        verbose_name=_("Варианты выбора"),
        help_text=_("Для типа 'select'. Каждый вариант с новой строки")
    )

    unit = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Единица измерения"),
        help_text=_("Например: В, А, МПа, кг, мм и т.д.")
    )

    # Дополнительные настройки
    is_required = models.BooleanField(
        default=False,
        verbose_name=_("Обязательное поле"),
        help_text=_("Характеристика обязательна для заполнения")
    )

    min_value = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Минимальное значение"),
        help_text=_("Минимальное значение (для чисел)")
    )

    max_value = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Максимальное значение"),
        help_text=_("Максимальное значение (для чисел)")
    )

    validation_regex = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Регулярное выражение"),
        help_text=_("Регулярное выражение для валидации текста")
    )

    default_value = models.TextField(
        blank=True,
        verbose_name=_("Значение по умолчанию"),
        help_text=_("Значение по умолчанию для этой характеристики")
    )

    help_text = models.TextField(
        blank=True,
        verbose_name=_("Подсказка для заполнения"),
        help_text=_("Подсказка для пользователя при заполнении")
    )

    class Meta:
        verbose_name = _("Вид характеристики")
        verbose_name_plural = _("Виды характеристик")
        ordering = ['sorting_order', 'name']

    def get_choices_list(self):
        """Получить список вариантов выбора"""
        if self.data_type == 'select' and self.choices:
            return [choice.strip() for choice in self.choices.split('\n') if choice.strip()]
        return []

    def get_equipment_types_list(self):
        """Получить список типов оборудования"""
        return ", ".join([et.name for et in self.equipment_types.all()])

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> dict:
        data = super().get_compact_data()
        data.update({
            'data_type': self.data_type,
            'data_type_display': self.get_data_type_display(),
            'unit': self.unit,
            'is_required': self.is_required,
            'equipment_types_count': self.equipment_types.count(),
        })
        return data

    def get_display_data(self, view_type: str = 'detail') -> dict:
        if view_type == self.LIST:
            return {
                'id': self.id,
                'name': self.name,
                'code': self.code,
                'data_type': self.get_data_type_display(),
                'unit': self.unit,
                'equipment_types': self.get_equipment_types_list(),
                'is_required': self.is_required,
                'is_active': self.is_active,
            }

        fields = self._get_base_display_fields()
        fields.update({
            'data_type': self._format_choice(
                self.data_type,
                self._meta.get_field('data_type').choices,
                label=_("Тип данных"),
                icon='📊',
                priority=5
            ),
            'unit': self._format_field(
                self.unit,
                'text',
                label=_("Единица измерения"),
                icon='📏',
                priority=6
            ),
            'is_required': self._format_boolean(
                self.is_required,
                label=_("Обязательное поле"),
                true_text=_("Да, обязательно"),
                false_text=_("Нет, необязательно"),
                icon='⚠️',
                priority=7
            ),
            'equipment_types': self._format_many_to_many(
                self.equipment_types.all(),
                label=_("Типы оборудования"),
                icon='⚙️',
                priority=8,
                include_data='compact'
            ),
            'default_value': self._format_field(
                self.default_value,
                'text',
                label=_("Значение по умолчанию"),
                icon='💾',
                priority=9,
                multiline=True
            ),
        })

        return {
            'title': self.name,
            'subtitle': f'{self.code} | {self.get_data_type_display()}',
            'fields': fields,
            'actions': self._get_actions()
        }