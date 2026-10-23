# ea_control/models/cu_power.py
"""
Справочники схемотехники цепей управления БУ (из черновика пользователя).

Зачем: физика цепей управления — откуда берётся питание сигналов управления,
какая логика работы (импульс/потенциал), какой тип сигнала на входе. Это
БУ-специфичные справочники: в ЭП-моделях их не было, они появятся здесь и
станут опциями новых слотов (SIGNAL_POWER_SOURCE, CONTROL_LOGIC, SIGNAL_TYPE).

Состав:

- ``CuSignalPowerSource`` — источник питания цепей управления О/С/З:
  встроенный (БУ сам выдаёт +24 В на общую клемму, внешнее питание не нужно)
  или внешний (цепи изолированы от внутренней логики, напряжение подаётся
  сторонней системой);
- ``CuSignalPower`` — пара «источник × напряжение цепей управления»
  (напряжение — глобальный справочник params.PowerSupplies, не копируем);
- ``CuControlLogic`` — доступная программная логика работы привода:
  импульсная (самоподхват), потенциальная, настраиваемая;
- ``CuSignalType`` — тип управляющего сигнала: сухой контакт, потенциал
  220 В и т.п., с типом логики и номиналом напряжения.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, LocalizedDictFieldsMixin


class CuSignalPowerSource(LocalizedDictFieldsMixin, CopyMixin):
    """Источник питания сигналов управления Открыть/Закрыть/Стоп БУ.

    Зачем: определяет схемотехнику входов — откуда цепи управления берут
    напряжение. Используется опцией слота SIGNAL_POWER_SOURCE и моделью
    CuSignalPower.

    Поля: code, name, description, sorting_order, is_active.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код источника, например «INTERNAL», «EXTERNAL»"),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Источник питания"),
        help_text=_("Встроенный (выдаётся приводом) / внешний (от сторонней "
                    "системы)"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание источника сигнала"),
        help_text=_("Например: БУ содержит собственный источник, на внешнюю "
                    "клемму общего провода выдаётся потенциал +24 В; внешнее "
                    "питание цепей автоматики не требуется."),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Источник питания сигналов управления БУ")
        verbose_name_plural = _("Источники питания сигналов управления БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class CuSignalPower(LocalizedDictFieldsMixin, CopyMixin):
    """Источник и напряжение цепей управления БУ.

    Зачем: связка «источник × номинал напряжения» цепей О/С/З (например,
    внешний источник 220 В AC или встроенный 24 В DC). Используется опцией
    слота SIGNAL_POWER_SOURCE и ControlUnit.signal_power.

    Поля: name, source (FK CuSignalPowerSource), power_supply
    (FK params.PowerSupplies — глобальный справочник напряжений, не копируем),
    description, sorting_order, is_active.
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Например: «Встроенный 24 В DC»"),
    )
    source = models.ForeignKey(
        CuSignalPowerSource, on_delete=models.PROTECT,
        related_name='signal_powers',
        verbose_name=_("Источник питания"),
        help_text=_("Встроенный или внешний источник цепей управления"),
    )
    power_supply = models.ForeignKey(
        'params.PowerSupplies', on_delete=models.PROTECT,
        related_name='cu_signal_powers',
        verbose_name=_("Напряжение цепей управления"),
        help_text=_("Номинал напряжения цепей управления БУ"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание схемотехники"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Питание цепей управления БУ")
        verbose_name_plural = _("Питания цепей управления БУ")
        ordering = ['sorting_order', 'id']
        unique_together = ['source', 'power_supply']

    def __str__(self):
        return self.name


class CuControlLogic(LocalizedDictFieldsMixin, CopyMixin):
    """Доступная программная логика работы привода.

    Зачем: как привод отрабатывает дискретные команды — импульсная логика
    (короткий импульс на клемму запускает процесс, плата «запоминает» команду
    на самоподхвате), потенциальная (команда выполняется, пока есть подача)
    или настраиваемая. Используется опцией слота CONTROL_LOGIC.

    Поля: code, name, has_self_holding (поддержка самоподхвата), description,
    sorting_order, is_active.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код логики, например «IMPULSE», «CONTINUOUS», "
                    "«CONFIGURABLE»"),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Логика работы привода"),
        help_text=_("Импульсная / потенциальная / настраиваемая"),
    )
    has_self_holding = models.BooleanField(
        default=False,
        verbose_name=_("Поддержка самоподхвата"),
        help_text=_("Плата запоминает команду и ведёт процесс до завершения"),
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Логика работы привода")
        verbose_name_plural = _("Логики работы привода")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class CuSignalType(LocalizedDictFieldsMixin, CopyMixin):
    """Тип управляющего сигнала на входе БУ.

    Зачем: какую форму имеет внешний сигнал управления — сухой контакт,
    потенциал 220 В AC и т.п. (например, модификация с потенциальными
    сигналами ~220 В: входы гальванически развязаны, внешние линии подключаются
    напрямую от термостатов/контакторов/ПЛК без промежуточных реле).
    Используется опцией слота SIGNAL_TYPE.

    Поля: code, name, logic_type (active_low/active_high), voltage
    (FK params.PowerSupplies — глобальный справочник напряжений),
    description, sorting_order, is_active.
    """
    LOGIC_CHOICES = (
        ('active_low', _('Active Low (NPN)')),
        ('active_high', _('Active High (PNP)')),
    )

    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код типа, например «DRY_CONTACT», «POT_220AC»"),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Тип сигнала"),
        help_text=_("Сухой контакт, потенциал 220 В AC и т.п."),
    )
    logic_type = models.CharField(
        max_length=20, choices=LOGIC_CHOICES,
        verbose_name=_("Тип логики"),
    )
    voltage = models.ForeignKey(
        'params.PowerSupplies', on_delete=models.PROTECT,
        related_name='cu_signal_types',
        verbose_name=_("Напряжение сигнала"),
        help_text=_("Номинал напряжения управляющего сигнала (глобальный "
                    "справочник напряжений)"),
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Тип управляющего сигнала БУ")
        verbose_name_plural = _("Типы управляющих сигналов БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return f"{self.name} ({self.get_logic_type_display()})"
