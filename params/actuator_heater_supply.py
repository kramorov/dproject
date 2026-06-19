# params/actuator_heater_supply.py
"""
Вариант питания обогрева электропривода.

Используется в схемах подключения (ControlUnitWiring) и других местах,
где нужно указать, от чего запитан антиконденсатный обогреватель привода:
  — Нет обогрева
  — От цепей питания устройства (общий кабель с двигателем)
  — От отдельной линии (выделенный кабель)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class ActuatorHeaterSupply(models.Model):
    """Вариант питания антиконденсатного обогрева электропривода."""
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Например: «От цепей питания устройства»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например «MOTOR_CIRCUIT»")
    )
    electrical_specs = models.CharField(
        max_length=255, blank=True,
        verbose_name=_("Электрические характеристики"),
        help_text=_("Например: «230В AC, 10 Вт» или «24В DC, 5 Вт»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Примечания к варианту питания обогрева")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Сортировка"),
        help_text=_("Порядок в списках выбора")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли в списках выбора")
    )

    class Meta:
        verbose_name = _("Питание обогрева привода")
        verbose_name_plural = _("Варианты питания обогрева привода")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name
