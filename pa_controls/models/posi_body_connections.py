# pa_controls/models/posi_body_connections.py
"""
Присоединения корпуса позиционера (PosiBodyConnections).

Справочник объединяет пару «резьба входа + резьба выхода» для пневмоподключения
корпуса позиционера (по образцу PneumaticActuatorBody для пневмоприводов):

    thread_in      — резьба входного отверстия (params.ThreadSize)
    thread_out     — резьба выходного отверстия (params.ThreadSize)
    cable_gland_hole — резьба отверстия под кабельный ввод (params.ThreadSize)

К серии позиционеров (PosiModelLine) привязывается через through-модель
PosiBodyConnectionOption (см. posi_model_line.py) вместо двух прежних опций
PosiPneumaticThreadOption и PosiPneumaticConnectionOption.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class PosiBodyConnections(models.Model):
    """Присоединения корпуса позиционера: резьбы пневмовхода/выхода + отверстие КВ."""

    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_('Текстовое название варианта присоединений корпуса позиционера')
    )
    code = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name=_("Код"),
        help_text=_("Код варианта присоединений")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_('Текстовое описание варианта присоединений')
    )
    thread_in = models.ForeignKey(
        'params.ThreadSize',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='posi_body_connections_thread_in',
        verbose_name=_("Пневмовход"),
        help_text=_('Резьба входного отверстия для пневмоподключения')
    )
    thread_out = models.ForeignKey(
        'params.ThreadSize',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='posi_body_connections_thread_out',
        verbose_name=_("Пневмовыход"),
        help_text=_('Резьба выходного отверстия для пневмоподключения')
    )
    cable_gland_hole = models.ForeignKey(
        'params.ThreadSize',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='posi_body_connections_cable_gland',
        verbose_name=_("Отверстие под кабельный ввод"),
        help_text=_('Резьба отверстия под кабельный ввод')
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Сортировка"),
        help_text=_('Порядок сортировки в списке')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_('Активно свойство или нет')
    )

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _('Присоединения корпуса позиционера')
        verbose_name_plural = _('Присоединения корпусов позиционеров')

    def __str__(self):
        return self.name
