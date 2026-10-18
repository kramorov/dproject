# electric_actuators/models/ea_access_device.py
"""Устройство ограничения несанкционированного доступа ЭП.

Справочник вариантов ``EaAccessDeviceOption`` (локализованный) + через-модель
``ControlUnitAccessDeviceOption`` (блок управления × вариант) с кодировками:
основной артикул не меняется (encoding пусто), ext-код — позиция ``{ad}``
(AD0 — устройства нет, AD1 — устройство есть). Участвует в хэше конфигурации
карточки каталога (config_hash_fields).
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


class ControlUnitAccessDeviceOption(models.Model):
    """Через-модель: блок управления × вариант устройства ограничения доступа.

    Для БУ basic (и «нет управления») доступен только NO_DEVICE; для
    остальных — NO_DEVICE (дефолт) и DEVICE. encoding — пусто (основной
    артикул не меняется), ext_encoding — позиция {ad} расширенного кода.
    """
    control_unit = models.ForeignKey(
        'params.ControlUnitInstalledOption',
        on_delete=models.CASCADE,
        related_name='access_device_options',
        verbose_name=_("Блок управления"),
        help_text=_("Блок управления, для которого доступен вариант")
    )
    access_device = models.ForeignKey(
        'EaAccessDeviceOption',
        on_delete=models.PROTECT,
        related_name='control_unit_options',
        verbose_name=_("Вариант устройства"),
        help_text=_("Вариант устройства ограничения доступа")
    )
    encoding = models.CharField(
        max_length=30, blank=True, default='',
        verbose_name=_("Кодировка"),
        help_text=_("Код для основного артикула (пусто — артикул не меняется)")
    )
    ext_encoding = models.CharField(
        max_length=10, blank=True, default='',
        verbose_name=_("Ext-код"),
        help_text=_("Код позиции {ad} расширенного кода: AD0 — нет, AD1 — есть")
    )
    is_default = models.BooleanField(default=False, verbose_name=_("Стандарт"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"))

    class Meta:
        verbose_name = _("Устройство ограничения доступа для БУ")
        verbose_name_plural = _("Устройства ограничения доступа для БУ")
        unique_together = ['control_unit', 'access_device']
        ordering = ['control_unit', 'sorting_order']

    def __str__(self):
        return f"{self.control_unit} → {self.access_device}"
