# electric_actuators/models/ea_signal_slot.py
"""
Справочник слотов (групп взаимоисключающих опций) матрицы сигналов ЭП.

``EaSignalSlot`` — группа single-choice в матрице доступности: в пределах
(скоуп × БУ × напряжение × режим) может быть выбрана не более одной строки
слота (``EaSignalMatrixEntry.slot``).

Примеры слотов:

    POSITION_FEEDBACK   — позиционная ОС (нет / потенциометр / трансмиттер / MWG…);
    LIMIT_SWITCHES      — концевые выключатели;
    WAY_SWITCHES        — путевые (промежуточные) выключатели;
    TORQUE_SWITCHES     — моментные выключатели;
    HEATER_ACTUATOR     — обогрев привода (нет / отдельная линия / от питания);
    HEATER_CONTROL_UNIT — обогрев блока управления (те же варианты);
    PROTOCOL            — шина (протокол связи БУ).

Слот — модель, а не строка-код: опечатка кода невозможна, обязательность
(``required``) и порядок слотов в UI хранятся в схеме. «Нет» внутри слота —
явная none-строка матрицы (signal=None), она считается доступной строкой.

Локализация: ru-базовые поля + ``_i18n``-переводы; коды не переводятся.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import (CopyMixin, LocalizedDictFieldsMixin,
                                 OptionListToSelectMixin)


class EaSignalSlot(CopyMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Слот матрицы сигналов ЭП — группа взаимоисключающих опций."""
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код слота, например «POSITION_FEEDBACK»")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название группы, например «Позиционная обратная связь»")
    )
    required = models.BooleanField(
        default=False,
        verbose_name=_("Обязательный"),
        help_text=_("В слоте должна быть хотя бы одна доступная строка "
                    "(none-строка «нет» считается доступной)")
    )
    multi_choice = models.BooleanField(
        default=False,
        verbose_name=_("Мультивыбор"),
        help_text=_("Слот допускает выбор нескольких опций одновременно "
                    "(например, CMD — команды О/С/З + Remote + Lock)")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение группы и правила выбора")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Слот сигналов ЭП")
        verbose_name_plural = _("Слоты сигналов ЭП")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name
