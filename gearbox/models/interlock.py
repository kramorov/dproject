#gearbox/models/interlock.py
# from typing import Dict

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, TemplateMixin

from pa_controls.models import LimitSwitchSensorVariety, SensorComponent
from params.models import IpOption


class GearBoxInterlock(CopyMixin, TemplateMixin, models.Model):
    """
    Блокировка/интерлок редуктора.

    Устройство контроля положения редуктора с датчиками:
    - Тип сенсора (``interlock_sensor_variety`` — механический, индуктивный…)
    - Датчики (``interlock_sensor_components`` — M2M на ``SensorComponent``)
    - Количество точек переключения (``interlock_points``, обычно 2 для SIL)
    - Степень защиты IP (``interlock_ip``) и взрывозащита (``interlock_exd``)

    Наследует ``CopyMixin`` и ``TemplateMixin``.
    """
    name = models.TextField(blank=True,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название модели интерлока редуктора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели редуктора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели интерлока редуктора'))

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    interlock_ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, null=True,
                                     related_name='gearbox_interlock_ip',
                                     help_text=_('Степень защиты IP интерлока'),
                                     verbose_name=_("IP")
                                     )
    interlock_exd = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='gearbox_interlock_exd',
        help_text=_('Степень взрывозащиты интерлока (можно выбрать несколько вариантов)'),
        verbose_name=_("Взрывозащита")
    )
    interlock_sensor_variety = models.ForeignKey(
        LimitSwitchSensorVariety, on_delete=models.SET_NULL, null=True,
        help_text=_('Тип сенсора интерлока'),
        verbose_name=_("Тип сенсора"), related_name='interlock_sensor_variety'
    )
    # Добавляем Many-to-Many связь с датчиками
    interlock_sensor_components = models.ManyToManyField(
        SensorComponent,
        blank=True,
        verbose_name=_("Датчики"),
        help_text=_("Установленные датчики интерлока"),
        related_name='interlock_sensor_components'  # обратная связь от датчика к корпусам
    )
    # Количество датчиков (иногда ставят 2 для избыточности/безопасности SIL)
    interlock_points = models.IntegerField(default=2,
                                           verbose_name=_("Количество датчиков"),
                                           help_text=_("Количество точек переключения (датчиков) интерлока")
                                           )
    class Meta:
        ordering = ['sorting_order', ]
        verbose_name = _('Интерлок')
        verbose_name_plural = _('Механизмы интерлоков')
    def __str__(self):
        return f"{self.name}"