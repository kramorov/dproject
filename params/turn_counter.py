# params/turn_counter.py
"""
Счётчики оборотов для многоборотных электроприводов.

Используются для определения конечных положений независимо от типа датчиков.
Один и тот же блок управления может работать с разными счётчиками.

Примеры записей:
- «Механический 187 оборотов»  (MECH-187T)
- «Электронный 1600 оборотов»  (ELEC-1600T)
- «Механический 4 оборота»     (MECH-4T)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import OptionListToSelectMixin


class TurnCounterOption(OptionListToSelectMixin, models.Model):
    """Счётчик оборотов — механический или электронный, с пределом по оборотам."""

    COUNTER_TYPES = [
        ('mechanical', _('Механический')),
        ('electronic', _('Электронный')),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Например: «Механический 187 оборотов»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например «MECH-187T»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Примечания по применению счётчика")
    )
    counter_type = models.CharField(
        max_length=20,
        choices=COUNTER_TYPES,
        default='mechanical',
        verbose_name=_("Тип счётчика"),
        help_text=_("Механический (кулачковый) или электронный (энкодерный)")
    )
    max_turns = models.PositiveSmallIntegerField(
        verbose_name=_("Максимальное число оборотов"),
        help_text=_("Предел счётчика по оборотам (0 … 32 000). "
                    "Например: 4, 187, 1600.")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки"),
        help_text=_("Порядок в списках выбора")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли в списках выбора")
    )

    class Meta:
        verbose_name = _("Счётчик оборотов")
        verbose_name_plural = _("Счётчики оборотов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name
