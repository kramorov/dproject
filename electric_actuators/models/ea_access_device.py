# electric_actuators/models/ea_access_device.py
"""Устройство ограничения несанкционированного доступа ЭП.

Справочник вариантов ``EaAccessDeviceOption`` (локализованный). Через-модель
``ControlUnitAccessDeviceOption`` удалена вместе с legacy-справочником БУ
(фаза 4.6): доступность устройства для БУ теперь выражается слотом
``ACCESS_DEVICE`` в слотовой модели ``ea_control``.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, LocalizedDictFieldsMixin


class EaAccessDeviceOption(CopyMixin, LocalizedDictFieldsMixin):
    """Вариант устройства ограничения несанкционированного доступа."""
    code = models.CharField(
        max_length=30, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код варианта (NO_DEVICE / DEVICE)")
    )
    name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Название"),
        help_text=_("Название варианта (ru)")
    )
    description = models.TextField(
        blank=True, verbose_name=_("Описание"),
        help_text=_("Пояснение варианта")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Устройство ограничения доступа (вариант)")
        verbose_name_plural = _("Устройства ограничения доступа (варианты)")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name

