# pa_controls/models/visual_indicator.py
"""
Справочник видов визуальных индикаторов положения БКВ.

VisualIndicatorType — вид индикатора («купол») на корпусе БКВ:
цвет купола и значение, которое он показывает в каждом положении.

Примеры:
  Купол, Зеленый — «Открыто», Красный — «Закрыто»
  Купол, Черный — «Открыто», Желтый — «Закрыто»
  Купол, Черный — «Открыто», Красный — «Закрыто»
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class VisualIndicatorType(models.Model):
    """Вид визуального индикатора положения (купол) БКВ."""
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_('Например: Купол, Зеленый — «Открыто», Красный — «Закрыто»')
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например DOME-GREEN-RED")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Примечания к виду индикатора")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Сортировка"),
        help_text=_("Порядок сортировки в списке")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли в списках выбора")
    )

    class Meta:
        verbose_name = _("Вид визуального индикатора")
        verbose_name_plural = _("Виды визуальных индикаторов")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name
