# electric_actuators/models/ea_slot_option.py
"""
Справочник опций слота матрицы сигналов ЭП (``EaSlotOption``).

Каждая запись — вариант, который может встречаться в слоте (``EaSignalSlot``):
сигнал (ОС/команда/протокол), питание обогрева или none-строка (опция без
клеммного сигнала: индикация, органы управления, счётчик, «нет датчика»).

Зачем: рабочая таблица матрицы (экспорт/импорт xlsx) и селекторы конфигуратора
нуждаются в **полном перечне опций слота** даже когда в матрице серии ещё нет
ни одной строки. Опции — записи с локализацией (плейсхолдеры шаблонов), без
хардкода.

``kind='pair'`` — пара контактов (END_SPDT и т.п.): раскрывается в ДВЕ строки
матрицы OPEN+CLOSE с общим ``bundle`` (код пары: ``PAIR:scope:mode``).
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, LocalizedDictFieldsMixin


class EaSlotOptionKind(models.TextChoices):
    """Тип опции слота."""
    SIGNAL = 'signal', _('Сигнал')
    HEATER = 'heater', _('Питание обогрева')
    NONE = 'none', _('Без сигнала (none-строка)')
    PAIR = 'pair', _('Пара контактов (Откр/Закр)')


class EaSlotOption(CopyMixin, LocalizedDictFieldsMixin):
    """Вариант опции в слоте матрицы сигналов ЭП."""
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код опции (для xlsx и ext-кода), "
                    "например «END_SPDT», «BLINKER», «NO_SENSOR»")
    )
    slot = models.ForeignKey(
        'EaSignalSlot', on_delete=models.CASCADE,
        related_name='slot_options',
        verbose_name=_("Слот"),
        help_text=_("Слот матрицы, к которому относится опция")
    )
    kind = models.CharField(
        max_length=10, choices=EaSlotOptionKind.choices,
        default=EaSlotOptionKind.SIGNAL,
        verbose_name=_("Тип опции"),
        help_text=_("signal — ссылка на сигнал/протокол; heater — питание "
                    "обогрева; none — опция без сигнала (имя); pair — пара "
                    "контактов Откр/Закр")
    )
    feedback_signal = models.ForeignKey(
        'EaFeedbackSignal', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Сигнал ОС"),
        help_text=_("Для kind=signal: выходной сигнал")
    )
    control_signal = models.ForeignKey(
        'EaControlSignal', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Командный сигнал"),
        help_text=_("Для kind=signal: входная команда (слоты CMD/SETPOINT)")
    )
    protocol = models.ForeignKey(
        'EaCommProtocol', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Протокол"),
        help_text=_("Для kind=signal: шина (слот PROTOCOL)")
    )
    heater_supply = models.ForeignKey(
        'params.ActuatorHeaterSupply', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Питание обогрева"),
        help_text=_("Для kind=heater (слот HEATER_CONTROL_UNIT)")
    )
    device = models.ForeignKey(
        'EaFeedbackDevice', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Устройство"),
        help_text=_("Датчик по умолчанию для опции (например, термореле)")
    )
    name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Название"),
        help_text=_("Для kind=none/pair: имя опции («Блинкер», «Селекторы»…)")
    )
    ext_encoding = models.CharField(
        max_length=10, blank=True, default='',
        verbose_name=_("Ext-код"),
        help_text=_("Код позиции расширенного кода заказа (ext): E1/E2, "
                    "W1/W2, T1/T2, P/T/TA, C/S, D/B/DB/L/LB, M/E/EM/MF/EMF…; "
                    "пусто — стандарт (позиция не кодируется)")
    )
    description = models.TextField(
        blank=True, verbose_name=_("Описание"),
        help_text=_("Пояснение опции")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Опция слота матрицы ЭП")
        verbose_name_plural = _("Опции слотов матрицы ЭП")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name or self.code

    def clean(self):
        super().clean()
        if self.kind == EaSlotOptionKind.SIGNAL:
            if sum(bool(x) for x in (self.feedback_signal_id,
                                     self.control_signal_id,
                                     self.protocol_id)) != 1:
                raise ValidationError(
                    _('Для опции-сигнала нужно ровно одно: сигнал ОС, команда '
                      'или протокол.'))
        elif self.kind == EaSlotOptionKind.HEATER:
            if not self.heater_supply_id:
                raise ValidationError(
                    _('Для опции-обогрева нужно питание обогрева.'))
        elif self.kind in (EaSlotOptionKind.NONE, EaSlotOptionKind.PAIR):
            if not self.name:
                raise ValidationError(
                    _('Для none/pair-опции нужно имя (название).'))
