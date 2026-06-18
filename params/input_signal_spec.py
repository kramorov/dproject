# params/input_signal_spec.py
"""
Спецификации входных сигналов блока управления.

InputSignalSpec описывает электрический интерфейс входного канала БУ:
  — дискретный вход 24В DC, оптронная развязка
  — аналоговый вход 4-20мА, 250 Ом
  — вход ESD, сухой контакт

Используется в ControlUnitSignalProfileEntry для входных ролей
(с direction='input'). Выходные роли используют SensorComponent.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class InputSignalSpec(models.Model):
    """Тип входного сигнала (канал) блока управления."""
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Например: «Дискретный вход БУ, 24В DC, оптронная развязка»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например «CU_DI_24V_OPTO»")
    )
    signal_category = models.CharField(
        max_length=20,
        choices=[
            ('discrete', _('Дискретный')),
            ('analog', _('Аналоговый')),
        ],
        verbose_name=_("Категория сигнала"),
        help_text=_("Дискретный (вкл/выкл) или аналоговый (4-20мА, 0-10В)")
    )
    electrical_specs = models.CharField(
        max_length=255, blank=True,
        verbose_name=_("Электрические характеристики"),
        help_text=_("Например: «24В DC, оптронная развязка, ~10мА» или «4-20мА, 250Ом»")
    )
    wires_count = models.PositiveSmallIntegerField(
        default=2,
        verbose_name=_("Кол-во проводов"),
        help_text=_("Количество жил для подключения этого входного сигнала")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Примечания к входному сигналу")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли в списках выбора")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Сортировка"),
        help_text=_("Порядок в списках выбора")
    )

    class Meta:
        verbose_name = _("Спецификация входного сигнала")
        verbose_name_plural = _("Спецификации входных сигналов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name
