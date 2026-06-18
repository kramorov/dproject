# params/signal_role.py
"""
Роли сигналов в конфигурации блока управления.

Каждая роль описывает смысловое назначение сигнала:
«Конечный Открыто», «Конечный Закрыто», «Момент Открыто»,
«4-20 мА положение», «Авария», «Готовность» и т.д.

Выходные роли привязываются к pa_controls.SensorComponent,
входные — к params.InputSignalSpec.
Связь роль → датчик/входной сигнал — через ControlUnitSignalProfileEntry.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models.mixins import CopyMixin


class SignalDirection(models.TextChoices):
    INPUT = 'input', _('Входной (команда приводу)')
    OUTPUT = 'output', _('Выходной (от привода)')


class SignalRole(CopyMixin, models.Model):
    """Роль сигнала в конфигурации БУ.

    Примеры:
        OPEN_LIMIT   — Конечный Открыто
        CLOSE_LIMIT  — Конечный Закрыто
        TORQUE_OPEN  — Момент Открыто
        TORQUE_CLOSE — Момент Закрыто
        POS_4_20MA   — 4-20 мА положение
        ALARM        — Авария
        READY        — Готовность
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Например: «Конечный Открыто»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например «OPEN_LIMIT»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Примечания к роли сигнала")
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
    direction = models.CharField(
        max_length=10,
        choices=SignalDirection.choices,
        default=SignalDirection.OUTPUT,
        verbose_name=_("Направление сигнала"),
        help_text=_("Входной — команда приводу от контроллера. "
                    "Выходной — обратная связь от привода.")
    )

    class Meta:
        verbose_name = _("Роль сигнала")
        verbose_name_plural = _("Роли сигналов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name