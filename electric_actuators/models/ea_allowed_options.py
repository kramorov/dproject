# electric_actuators/models/ea_allowed_options.py
"""
Разрешённые опции на уровне серии (model_line).

Хранят encoding для пары (серия, опция) — единый источник истины
для всей серии. Справочник разрешённых БУ (``AllowedControlUnitOption``)
удалён: БУ теперь в слотовой модели ``ea_control`` (``ControlUnit`` +
``ControlUnitBinding`` + матрица подтипа).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class AllowedTurnCounterOption(models.Model):
    """Счётчик оборотов, разрешённый для серии, с кодировкой."""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='allowed_turn_counters',
        verbose_name=_("Серия"),
        help_text=_("Серия электроприводов")
    )
    turn_counter = models.ForeignKey(
        'params.TurnCounterOption',
        on_delete=models.CASCADE,
        related_name='allowed_in_model_lines',
        verbose_name=_("Счётчик оборотов")
    )
    encoding = models.CharField(
        max_length=50,
        verbose_name=_("Кодировка"),
        help_text=_("Код для подстановки в артикул")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))

    class Meta:
        verbose_name = _("Разрешённый счётчик для серии")
        verbose_name_plural = _("Разрешённые счётчики для серий")
        unique_together = ['model_line', 'turn_counter']
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.model_line} → {self.turn_counter} ({self.encoding})"

