# electric_actuators/models/ea_comm_protocol.py
"""
Справочник шинных протоколов связи блоков управления электроприводов.

``EaCommProtocol`` — двунаправленные цифровые протоколы (шины): один канал несёт
и команды, и обратную связь, поэтому они висят на блоке управления
(``EaControlUnit.protocols`` / слот PROTOCOL матрицы), а не на сигналах.

HART сюда НЕ входит: он едет по петле 4–20 мА и моделируется атрибутом
``hart=True`` на сигнале (см. ``EaControlSignal``/``EaFeedbackSignal``).

Modbus RTU и Modbus TCP — разные записи справочника (разный транспорт);
``transport`` — справочная характеристика канала.

Локализация: ru-базовые поля + ``_i18n``-переводы; коды не переводятся.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import (CopyMixin, LocalizedDictFieldsMixin,
                                 OptionListToSelectMixin)


class EaProtocolTransport(models.TextChoices):
    """Транспорт шины."""
    RS485 = 'rs485', _('RS-485')
    ETHERNET = 'ethernet', _('Ethernet')
    CURRENT_LOOP = 'current_loop', _('Токовая петля (20 мА)')
    H1 = 'h1', _('Fieldbus H1')
    OTHER = 'other', _('Прочее')


class EaCommProtocol(CopyMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Шинный протокол связи БУ электропривода.

    Примеры: MODBUS_RTU, MODBUS_TCP, PROFIBUS_DP, PROFINET,
    FOUNDATION_FIELDBUS, PAKSCAN, DEVICENET, ETHERNET_IP.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код протокола, например «MODBUS_RTU»")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название протокола, например «Modbus RTU»")
    )
    transport = models.CharField(
        max_length=20, choices=EaProtocolTransport.choices,
        verbose_name=_("Транспорт"),
        help_text=_("Физический транспорт шины (RS-485, Ethernet, …)")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Краткая характеристика канала (скорость, топология, примечания)")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Протокол связи ЭП")
        verbose_name_plural = _("Протоколы связи ЭП")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name
