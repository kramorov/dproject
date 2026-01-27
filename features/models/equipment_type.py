# features/models/equipment_type.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseAbstractModel


class EquipmentType(BaseAbstractModel):
    """
    Тип оборудования (классификатор)
    Примеры: 'Пневмопривод', 'Электропривод', 'Клапан', 'Задвижка'
    """
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Родительский тип"),
        help_text=_("Родительский тип оборудования для иерархии")
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Иконка"),
        help_text=_("Иконка для отображения (emoji или название класса CSS)")
    )

    # Уровень в иерархии (для удобства)
    level = models.IntegerField(
        default=0,
        verbose_name=_("Уровень иерархии"),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    class Meta:
        verbose_name = _("Тип оборудования")
        verbose_name_plural = _("Типы оборудования")
        ordering = ['level', 'sorting_order', 'name']

    def save(self, *args, **kwargs):
        """Автоматически вычисляем уровень при сохранении"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
        super().save(*args, **kwargs)

    def get_full_path(self):
        """Получить полный путь в иерархии"""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " → ".join(path)

    def get_children_count(self):
        """Количество дочерних элементов"""
        return self.children.count()

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> dict:
        data = super().get_compact_data()
        data.update({
            'level': self.level,
            'parent_id': self.parent_id,
            'icon': self.icon,
            'full_path': self.get_full_path(),
            'children_count': self.get_children_count(),
        })
        return data

    def get_display_data(self, view_type: str = 'detail') -> dict:
        if view_type == self.LIST:
            return {
                'id': self.id,
                'name': self.name,
                'code': self.code,
                'level': self.level,
                'full_path': self.get_full_path(),
                'is_active': self.is_active,
                'children_count': self.get_children_count(),
            }

        fields = self._get_base_display_fields()
        fields.update({
            'parent': self._format_foreign_key(
                self.parent,
                label=_("Родительский тип"),
                icon='↕️',
                priority=5,
                include_data='compact'
            ),
            'level': self._format_field(
                self.level,
                'number',
                label=_("Уровень иерархии"),
                icon='📊',
                priority=6
            ),
            'icon': self._format_field(
                self.icon,
                'text',
                label=_("Иконка"),
                icon='🎨',
                priority=7
            ),
            'children': self._format_many_to_many(
                self.children.all(),
                label=_("Дочерние типы"),
                icon='📂',
                priority=8,
                include_data='compact'
            ),
        })

        return {
            'title': self.name,
            'subtitle': f'{self.get_full_path()}',
            'fields': fields,
            'actions': self._get_actions()
        }