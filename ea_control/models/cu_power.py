# ea_control/models/cu_power.py
"""
Справочники схемотехники цепей управления БУ (из черновика пользователя).

Зачем: физика цепей управления — откуда берётся питание сигналов управления,
какая логика работы (импульс/потенциал/настраиваемая), какая схема входа
(источник × напряжение × форма × полярность). Это БУ-специфичные справочники:
в ЭП-моделях их не было, они появились здесь и стали опциями слотов узла
«Дистанционное управление» (CMD_WIRING + сигнальные слоты с опциями-логиками).

Состав:

- ``CuSignalPowerSource`` — источник питания цепей управления О/С/З:
  встроенный (БУ сам выдаёт +24 В на общую клемму, внешнее питание не нужно)
  или внешний (цепи изолированы от внутренней логики, напряжение подаётся
  сторонней системой);
- ``CuSignalPower`` — схема цепей: «источник × напряжение × форма входных
  цепей × полярность» (напряжение — глобальный справочник
  params.PowerSupplies, не копируем);
- ``CuPolarity`` — словарь полярности входов (PNP/NPN/двунаправленный/
  не применимо);
- ``CuControlLogic`` — доступная программная логика работы привода:
  импульсная (самоподхват), потенциальная, настраиваемая.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import (CopyMixin, LocalizedDictFieldsMixin,
                                 OptionListToSelectMixin)


class CuSignalPowerSource(LocalizedDictFieldsMixin, CopyMixin):
    """Источник питания сигналов управления Открыть/Закрыть/Стоп БУ.

    Зачем: определяет схемотехнику входов — откуда цепи управления берут
    напряжение. Используется опцией слота CMD_WIRING (через CuSignalPower)
    и моделью CuSignalPower.

    Поля: code, name, internal (встроенный — БУ сам выдаёт опорное
    напряжение на общую клемму), description, sorting_order, is_active.
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
    internal = models.BooleanField(
        default=False,
        verbose_name=_("Встроенный источник"),
        help_text=_("БУ сам выдаёт опорное напряжение на общую клемму; "
                    "входы команд — сухие контакты с внутренним опросом"),
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


POLARITIES = (
    ('PNP', 'PNP — плюс-управление (активный высокий)'),
    ('NPN', 'NPN — минус-управление (активный низкий)'),
    ('BIDIRECTIONAL', 'Двунаправленный (DC, любая полярность)'),
    ('NOT_APPLICABLE', 'Не применимо (AC или сухой контакт)'),
)


class CuPolarity(CopyMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Полярность входных цепей управления (DC-схемы).

    Терминология автоматизации: PNP/NPN описывают, каким проводом внешняя
    сторона управляет сигнальной линией (к полупроводникам БУ отношения
    не имеет; названия исторические — от выходных каскадов датчиков):

    - PNP («плюс-управление», активный высокий): команда активна, когда на
      клемме входа положительный потенциал (+24/+110 В DC) относительно
      общего провода — внешняя сторона коммутирует плюсовой провод;
    - NPN («минус-управление», активный низкий): команда активна, когда
      клемма замкнута на общий провод (0 В) — внешняя сторона коммутирует
      минусовой провод;
    - Двунаправленный: вход срабатывает при любой полярности DC;
    - Не применимо: цепь AC (полярности нет) или сухой контакт (опрос задан
      внутри БУ и наружу не виден).

    Раньше была ``models.TextChoices`` — заменена на справочную модель.
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Полярность входных цепей")
        verbose_name_plural = _("Полярности входных цепей")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


def _default_polarity():
    """Дефолтная полярность: не применимо (как было до перевода на FK)."""
    obj, _ = CuPolarity.objects.get_or_create(
        code='NOT_APPLICABLE',
        defaults={'name': 'Не применимо (AC или сухой контакт)'})
    return obj.pk


class CuSignalPower(LocalizedDictFieldsMixin, CopyMixin):
    """Схема цепей управления БУ: источник × напряжение × форма × полярность.

    Зачем: опция слота CMD_WIRING («Схема цепей управления») — как внешняя
    цепь подаёт дискретные команды О/С/З/ESD: сухими контактами с внутренним
    опросом БУ (+24 В от внутреннего источника) или потенциалом AC/DC от
    внешнего источника. Используется опцией слота CMD_WIRING
    и координатой ``signal_power`` строк матрицы («набор сигналов —
    опции схемы»).

    Поля: name, source (FK CuSignalPowerSource), power_supply
    (FK params.PowerSupplies — глобальный справочник напряжений),
    input_form (FK CuControlSignalForm — форма входных цепей пары),
    polarity (CuPolarity), description, sorting_order, is_active.
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Например: «Внутренний +24 В (сухой контакт)», "
                    "«Внешний 220 В AC»"),
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
    input_form = models.ForeignKey(
        'CuControlSignalForm', on_delete=models.PROTECT, null=True, blank=True,
        related_name='signal_powers',
        verbose_name=_("Форма входных цепей"),
        help_text=_("Как внешняя цепь подаёт команду в этой схеме: сухой "
                    "контакт (DRY_INPUT) / потенциал AC (VOLTAGE_AC) / "
                    "потенциал DC (VOLTAGE_DC); null — пара не про входы "
                    "команд"),
    )
    polarity = models.ForeignKey(
        CuPolarity, on_delete=models.PROTECT,
        default=_default_polarity,
        related_name='signal_powers',
        verbose_name=_("Полярность"),
        help_text=_( 'PNP («плюс-управление», активный высокий): команда активна, ' 'когда на клемме входа положительный потенциал (+24/+110 В DC) ' 'относительно общего провода — внешняя сторона коммутирует ' 'плюсовой провод. ' 'NPN («минус-управление», активный низкий): команда активна, ' 'когда клемма замкнута на общий провод (0 В) — внешняя сторона ' 'коммутирует минусовой провод. ' 'Двунаправленный: вход срабатывает при любой полярности DC. ' 'Не применимо: цепь AC (полярности нет) или сухой контакт ' '(опрос задан внутри БУ и наружу не виден).' ),
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
        unique_together = ['source', 'power_supply', 'input_form', 'polarity']
        constraints = [
            # в SQLite NULL в уникальном индексе «не равен себе» — пары без
            # формы входа защищаем условным ограничением (частичный индекс)
            models.UniqueConstraint(
                fields=['source', 'power_supply', 'polarity'],
                condition=models.Q(input_form__isnull=True),
                name='cu_signalpower_null_input_form_unique'),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.input_form_id:
            category = self.input_form.category.code
            if category == 'dry_input' \
                    and not getattr(self.source, 'internal', False):
                raise ValidationError(
                    {'input_form': _('Сухой контакт (внутренний опрос) — '
                                     'только со встроенным источником.')})
            if category == 'voltage_ac' and not str(
                    self.power_supply.code or '').endswith('-AC'):
                raise ValidationError(
                    {'power_supply': _('Для формы «Потенциал AC» нужно '
                                       'напряжение переменного тока (код '
                                       '*-AC).')})
            if category == 'voltage_dc' and not str(
                    self.power_supply.code or '').endswith('-DC'):
                raise ValidationError(
                    {'power_supply': _('Для формы «Потенциал DC» нужно '
                                       'напряжение постоянного тока (код '
                                       '*-DC).')})
        if self.input_form_id and self.input_form.category.code in (
                'dry_input', 'voltage_ac') \
                and self.polarity.code != 'NOT_APPLICABLE':
            raise ValidationError(
                {'polarity': _('Для сухого контакта и цепей AC полярность '
                               'не применима.')})


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
