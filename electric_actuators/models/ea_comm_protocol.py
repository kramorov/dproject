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


# Единый набор транспортов шины (ЭП + БУ; коды в нижнем регистре).
PROTOCOL_TRANSPORTS = (
    ('rs485', 'RS-485'),
    ('ethernet', 'Ethernet'),
    ('current_loop', 'Токовая петля (20 мА)'),
    ('h1', 'Fieldbus H1'),
    ('other', 'Прочее'),
)


class EaProtocolTransport(CopyMixin, LocalizedDictFieldsMixin,
                          OptionListToSelectMixin):
    """Транспорт шины.

    Раньше была ``models.TextChoices`` — заменена на справочную модель;
    общая для ЭП и БУ (коды БУ RS485/ETHERNET/OTHER приведены к нижнему
    регистру ЭП).
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Транспорт протокола")
        verbose_name_plural = _("Транспорты протоколов")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


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
    transport = models.ForeignKey(
        EaProtocolTransport, on_delete=models.PROTECT,
        related_name='protocols',
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
