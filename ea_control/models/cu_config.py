# ea_control/models/cu_config.py
"""
Конкретные паттерн-модели конфигурации БУ (наследники абстракций).

Каждая модель здесь — реализация одной роли паттерна для домена БУ
(slots.md → «План: отладка паттерна…»):

- ``CuSectionNode`` ← AbstractConfigNode — дерево узлов-секций БУ;
- ``CuSlot`` ← AbstractConfigSlot — слоты конфигурации БУ;
- ``CuSlotOption`` ← AbstractSlotOption — опции слотов БУ;
- ``CuMatrixEntry`` ← AbstractSlotMatrixEntry — матрица доступности;
- ``CuSlotRule`` ← AbstractSlotRule — динамика конфигуратора (Паттерн В).

Профиль БУ (шаблон) — не отдельная модель: это бесскоуповые строки матрицы
(все поля скоупа пустые) — дефолты слотов для типа БУ.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import LocalizedDictFieldsMixin
from core.utils.localization import localized_name, pick_i18n

from ea_control.models.abstract import (AbstractConfigNode, AbstractConfigSlot,
                                        AbstractSlotMatrixEntry,
                                        AbstractSlotOption, AbstractSlotRule)


class CuSectionNode(LocalizedDictFieldsMixin, AbstractConfigNode):
    """Узел-секция конфигурации БУ (роль ``Node``).

    Зачем: дерево секций, по которому конфигуратор рисует разделы:
    УПРАВЛЕНИЕ / ОБРАТНАЯ СВЯЗЬ / СВЯЗЬ / ПИТАНИЕ (с вложенностью).
    Относительно AbstractConfigNode полей не добавлено — связь слотов идёт
    обратной стороной (CuSlot.section).
    """

    class Meta:
        verbose_name = _("Узел-секция БУ")
        verbose_name_plural = _("Узлы-секции БУ")
        ordering = ['sorting_order', 'code']


class CuSlot(LocalizedDictFieldsMixin, AbstractConfigSlot):
    """Слот конфигурации БУ (роль ``Slot``).

    Зачем: точка выбора в конфигураторе БУ. Коды сигнальных слотов совпадают
    с EaSignalSlot (LOCAL_CONTROL/SETPOINT/LIMIT_SWITCHES/WAY_SWITCHES/
    TORQUE_SWITCHES/POSITION_FEEDBACK/THERMAL_SENSOR/INDICATOR/TURN_COUNTER/
    PROTOCOL/HEATER_CONTROL_UNIT) — они ключи маппинга при миграции; плюс
    БУ-специфичные слоты дистанционного управления (CMD_WIRING и
    CMD_OPEN/CMD_CLOSE/CMD_STOP/CMD_ESD) и слот ``control_unit``
    (slot_kind=object) — выбор типа БУ.

    Добавлено относительно AbstractConfigSlot:

    - ``section`` — FK на узел-секцию (дерево конфигуратора).
    """
    section = models.ForeignKey(
        CuSectionNode, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='slots',
        verbose_name=_("Узел-секция"),
        help_text=_("Раздел дерева конфигуратора, к которому привязан слот"),
    )

    class Meta:
        verbose_name = _("Слот БУ")
        verbose_name_plural = _("Слоты БУ")
        ordering = ['sorting_order', 'code']


class CuOptionKind(models.TextChoices):
    """Тип опции слота БУ (значения домена, переопределяют абстрактный kind)."""
    SIGNAL = 'signal', _('Сигнал')
    DEVICE = 'device', _('Устройство ОС')
    HEATER = 'heater', _('Питание обогрева')
    POWER = 'power', _('Схема цепей управления (источник × напряжение)')
    LOGIC = 'logic', _('Логика работы сигнала')
    UNIT = 'unit', _('Блок управления (слот control_unit)')
    LOCAL_CONTROL = 'local_control', _('Орган местного управления')
    DISPLAY = 'display', _('Вид отображения')
    UNIT_POWER = 'unit_power', _('Питание БУ')
    CABLE_GLAND = 'cable_gland', _('Кабельные вводы БУ')
    LOCATION = 'location', _('Размещение БУ')
    NONE = 'none', _('Без сигнала (none-строка)')
    PAIR = 'pair', _('Пара контактов (Откр/Закр)')


class CuSlotOption(LocalizedDictFieldsMixin, AbstractSlotOption):
    """Опция слота БУ (роль ``Option``).

    Зачем: справочник возможных вариантов заполнения слота. Опция не хранит
    доступность — это строки матрицы; опция описывает «что это за вариант» и
    ссылается на физическую сущность по ``kind``.

    Добавлено относительно AbstractSlotOption:

    - ``slot`` — FK на слот (обратная связь related_name='slot_options');
    - ``kind`` — переопределён словарём домена CuOptionKind;
    - типизированные полезные нагрузки по kind: ``control_signal`` /
      ``feedback_signal`` / ``protocol`` (signal), ``heater_supply``
      (heater), ``signal_power`` (power — схема цепей управления),
      ``control_logic`` (logic — логика сигнала), ``control_unit`` (unit —
      только для слота control_unit), ``device`` (датчик по умолчанию для
      опции), ``location_option`` (location — размещение БУ, слот
      CU_LOCATION);
    - ``clean()`` — ровно одна полезная нагрузка на kind (образец
      EaSlotOption.clean).
    """
    slot = models.ForeignKey(
        CuSlot, on_delete=models.CASCADE,
        related_name='slot_options',
        verbose_name=_("Слот"),
        help_text=_("Слот, к которому относится опция"),
    )
    kind = models.CharField(
        max_length=20, choices=CuOptionKind.choices,
        default=CuOptionKind.SIGNAL,
        verbose_name=_("Тип опции"),
        help_text=_("signal — сигнал/протокол; heater — обогрев; power — "
                    "схема цепей управления; logic — логика работы; unit — "
                    "БУ (слот control_unit); local_control — орган местного "
                    "управления; display — вид(ы) отображения; unit_power — "
                    "питание БУ; cable_gland — резьба кабельных вводов БУ; "
                    "location — размещение БУ; none — опция без полезной "
                    "нагрузки; pair — пара контактов Откр/Закр"),
    )
    control_signal = models.ForeignKey(
        'CuControlSignal', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Командный сигнал"),
        help_text=_("Для kind=signal: входная команда (слоты CMD/SETPOINT)"),
    )
    feedback_signal = models.ForeignKey(
        'CuFeedbackSignal', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Сигнал ОС"),
        help_text=_("Для kind=signal: выходной сигнал"),
    )
    protocol = models.ForeignKey(
        'CuCommProtocol', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Протокол"),
        help_text=_("Для kind=signal: шина (слот PROTOCOL)"),
    )
    heater_supply = models.ForeignKey(
        'CuHeaterSupply', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Питание обогрева"),
        help_text=_("Для kind=heater (слот HEATER_CONTROL_UNIT)"),
    )
    signal_power = models.ForeignKey(
        'CuSignalPower', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Схема цепей управления"),
        help_text=_("Для kind=power (слот CMD_WIRING «Схема цепей "
                    "управления»): источник × напряжение × форма × полярность"),
    )
    control_logic = models.ForeignKey(
        'CuControlLogic', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Логика работы"),
        help_text=_("Для kind=logic: логика сигнала (импульсная/потенциальная/"
                    "настраиваемая) — опции слотов команд CMD_OPEN/CLOSE/"
                    "STOP/ESD"),
    )
    control_unit = models.ForeignKey(
        'ControlUnit', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Блок управления"),
        help_text=_("Для kind=unit: опция слота control_unit — тип БУ"),
    )
    device = models.ForeignKey(
        'CuFeedbackDevice', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Устройство"),
        help_text=_("Датчик по умолчанию для опции (например, термореле)"),
    )
    local_control_type = models.ForeignKey(
        'CuLocalControlType', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Орган местного управления"),
        help_text=_("Для kind=local_control: кнопки/селекторы (слот "
                    "LOCAL_CONTROL_DESIGN узла «Местная индикация»)"),
    )
    display_types = models.ManyToManyField(
        'CuDisplayType', blank=True,
        related_name='slot_options',
        verbose_name=_("Виды отображения"),
        help_text=_("Для kind=display: один или несколько видов отображения "
                    "(слоты сигналов индикации; комбинация — например, "
                    "«на LCD + мигающий светодиод»)"),
    )
    unit_power_source = models.ForeignKey(
        'CuUnitPowerSource', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Питание БУ"),
        help_text=_("Для kind=unit_power: общий кабель с приводом или "
                    "отдельный кабель (слот CU_POWER_SUPPLY)"),
    )
    cable_gland_set = models.ForeignKey(
        'params.ThreadSizeSet', on_delete=models.PROTECT, null=True, blank=True,
        related_name='cu_slot_options',
        verbose_name=_("Набор резьб кабельных вводов БУ"),
        help_text=_("Для kind=cable_gland: набор резьбовых отверстий ввода "
                    "кабелей БУ (глобальный справочник params.ThreadSizeSet — "
                    "каждая резьба с количеством; слот CU_CABLE_GLANDS)"),
    )
    location_option = models.ForeignKey(
        'CuLocationOption', on_delete=models.PROTECT, null=True, blank=True,
        related_name='slot_options',
        verbose_name=_("Размещение БУ"),
        help_text=_("Для kind=location: место размещения БУ (встроен/навесной; "
                    "слот CU_LOCATION)"),
    )

    class Meta:
        verbose_name = _("Опция слота БУ")
        verbose_name_plural = _("Опции слотов БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        if self.kind == CuOptionKind.UNIT and self.control_unit_id:
            return str(self.control_unit)
        if self.kind == CuOptionKind.LOCAL_CONTROL and self.local_control_type_id:
            return str(self.local_control_type)
        if self.kind == CuOptionKind.UNIT_POWER and self.unit_power_source_id:
            return str(self.unit_power_source)
        if self.kind == CuOptionKind.CABLE_GLAND and self.cable_gland_set_id:
            return str(self.cable_gland_set)
        if self.kind == CuOptionKind.LOCATION and self.location_option_id:
            return str(self.location_option)
        if self.kind == CuOptionKind.DEVICE and self.device_id:
            return str(self.device)
        if self.kind == CuOptionKind.DISPLAY:
            names = [str(d) for d in self.display_types.all().order_by('sorting_order')]
            if names:
                return ' + '.join(names)
        return self.name or self.code

    def localized_name(self, locale=None):
        """Имя опции; для типизированных kind — имя сущности нагрузки."""
        if self.kind == CuOptionKind.UNIT and self.control_unit_id:
            return localized_name(self.control_unit, locale)
        if self.kind == CuOptionKind.LOCAL_CONTROL and self.local_control_type_id:
            return localized_name(self.local_control_type, locale)
        if self.kind == CuOptionKind.UNIT_POWER and self.unit_power_source_id:
            return localized_name(self.unit_power_source, locale)
        if self.kind == CuOptionKind.CABLE_GLAND and self.cable_gland_set_id:
            return localized_name(self.cable_gland_set, locale)
        if self.kind == CuOptionKind.LOCATION and self.location_option_id:
            return localized_name(self.location_option, locale)
        if self.kind == CuOptionKind.DEVICE and self.device_id:
            return localized_name(self.device, locale)
        if self.kind == CuOptionKind.POWER and self.signal_power_id:
            return localized_name(self.signal_power, locale)
        if self.kind == CuOptionKind.LOGIC and self.control_logic_id:
            return localized_name(self.control_logic, locale)
        if self.kind == CuOptionKind.HEATER and self.heater_supply_id:
            return localized_name(self.heater_supply, locale)
        if self.kind == CuOptionKind.SIGNAL:
            for fk in ('control_signal', 'feedback_signal', 'protocol'):
                obj = getattr(self, fk, None)
                if obj is not None:
                    return localized_name(obj, locale)
        if self.kind == CuOptionKind.DISPLAY:
            names = [localized_name(d, locale)
                     for d in self.display_types.all().order_by('sorting_order')]
            if names:
                return ' + '.join(names)
        return pick_i18n(self.name_i18n, locale, fallback=self.name or self.code)

    def clean(self):
        super().clean()
        if self.kind == CuOptionKind.SIGNAL:
            if sum(bool(x) for x in (self.control_signal_id,
                                     self.feedback_signal_id,
                                     self.protocol_id)) != 1:
                raise ValidationError(
                    _('Для опции-сигнала нужно ровно одно: сигнал ОС, команда '
                      'или протокол.'))
        elif self.kind == CuOptionKind.HEATER:
            if not self.heater_supply_id:
                raise ValidationError(_('Для опции-обогрева нужно питание обогрева.'))
        elif self.kind == CuOptionKind.DEVICE:
            if not self.device_id:
                raise ValidationError(_('Для опции-устройства нужно устройство ОС.'))
        elif self.kind == CuOptionKind.POWER:
            if not self.signal_power_id:
                raise ValidationError(_('Для опции питания цепей нужно CuSignalPower.'))
        elif self.kind == CuOptionKind.LOGIC:
            if not self.control_logic_id:
                raise ValidationError(_('Для опции логики нужна CuControlLogic.'))
        elif self.kind == CuOptionKind.UNIT:
            if not self.control_unit_id:
                raise ValidationError(_('Для опции-БУ нужен ControlUnit.'))
            if self.slot.code != 'control_unit':
                raise ValidationError(
                    {'control_unit': _('Опция-БУ допустима только в слоте '
                                       'control_unit.')})
        elif self.kind == CuOptionKind.LOCAL_CONTROL:
            if not self.local_control_type_id:
                raise ValidationError(
                    _('Для опции органа управления нужен CuLocalControlType.'))
        elif self.kind == CuOptionKind.DISPLAY:
            # M2M сохраняется после clean() (админка) — проверяем только
            # для уже сохранённых объектов, чтобы не ломать создание.
            if self.pk and not self.display_types.exists():
                raise ValidationError(
                    _('Для опции отображения нужен хотя бы один вид отображения.'))
        elif self.kind == CuOptionKind.UNIT_POWER:
            if not self.unit_power_source_id:
                raise ValidationError(
                    _('Для опции питания БУ нужен CuUnitPowerSource.'))
        elif self.kind == CuOptionKind.CABLE_GLAND:
            if not self.cable_gland_set_id:
                raise ValidationError(
                    _('Для опции кабельных вводов нужен набор резьб '
                      '(params.ThreadSizeSet).'))
        elif self.kind == CuOptionKind.LOCATION:
            if not self.location_option_id:
                raise ValidationError(
                    _('Для опции размещения нужен CuLocationOption.'))
        elif self.kind in (CuOptionKind.NONE, CuOptionKind.PAIR):
            if not self.name:
                raise ValidationError(_('Для none/pair-опции нужно имя (название).'))


class CuMatrixMode(models.TextChoices):
    """Режим работы, для которого актуальна строка матрицы."""
    ON_OFF = 'on_off', _('Двухпозиционный (on-off)')
    MODULATING = 'modulating', _('Модулирующий')
    BOTH = 'both', _('Оба режима')


class CuMatrixEntry(LocalizedDictFieldsMixin, AbstractSlotMatrixEntry):
    """Строка матрицы доступности БУ (Паттерн А).

    Зачем: ответ «доступна ли опция X в точке Y». Точка Y — скоуп
    (бренд/серия/корпус/модель) + координаты (БУ × напряжение × режим).
    Строки с пустым скоупом — профиль типа БУ (дефолты слотов); строка
    ``availability=na`` на специфичном уровне запрещает унаследованную.

    Добавлено относительно AbstractSlotMatrixEntry:

    - ``slot``/``option`` — FK на слот и опцию (option.slot должен
      совпадать со slot — проверка в clean);
    - скоуп: ``brand`` (producers.Brands) / ``model_line``
      (ElectricActuatorModelLine) / ``body`` (ElectricActuatorBody) /
      ``model_line_item`` (ElectricActuatorModelLineItem) — ровно один или
      все пустые (CheckConstraint «один скоуп»);
    - координаты: ``control_unit`` (ControlUnit, null — для строк слота
      control_unit и профильных строк), ``power_supply`` (params.PowerSupplies,
      null — любое напряжение), ``signal_power`` (CuSignalPower — схема цепей
      управления; null — любая схема; «набор сигналов — опции схемы»),
      ``mode`` (CuMatrixMode);
    - полезные нагрузки строки: ``control_signal``/``feedback_signal``/
      ``protocol``/``device``/``heater_supply`` — типизированные FK
      (CheckConstraint «одна нагрузка»);
    - ``clean()`` — протокол только для слота PROTOCOL, обогрев только для
      HEATER_*, устройство только с сигналом ОС (device.emits содержит его);
    - ``_base_name()`` — имя из полезной нагрузки (сигнал/устройство/БУ).
    """
    slot = models.ForeignKey(
        CuSlot, on_delete=models.PROTECT,
        related_name='matrix_rows',
        verbose_name=_("Слот"),
        help_text=_("Группа взаимоисключающих опций (single-choice)"),
    )
    option = models.ForeignKey(
        CuSlotOption, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Опция слота"),
        help_text=_("Ссылка на каталог опций слота; пусто — строка вне каталога"),
    )
    brand = models.ForeignKey(
        'producers.Brands', on_delete=models.CASCADE, null=True, blank=True,
        related_name='cu_matrix_rows',
        verbose_name=_("Бренд"),
        help_text=_("Уровень скоупа «бренд»"),
    )
    model_line = models.ForeignKey(
        'electric_actuators.ElectricActuatorModelLine',
        on_delete=models.CASCADE, null=True, blank=True,
        related_name='cu_matrix_rows',
        verbose_name=_("Серия"),
        help_text=_("Уровень скоупа «серия»"),
    )
    body = models.ForeignKey(
        'electric_actuators.ElectricActuatorBody',
        on_delete=models.CASCADE, null=True, blank=True,
        related_name='cu_matrix_rows',
        verbose_name=_("Корпус"),
        help_text=_("Уровень скоупа «корпус»"),
    )
    model_line_item = models.ForeignKey(
        'electric_actuators.ElectricActuatorModelLineItem',
        on_delete=models.CASCADE, null=True, blank=True,
        related_name='cu_matrix_rows',
        verbose_name=_("Модель"),
        help_text=_("Уровень скоупа «модель» (самый специфичный)"),
    )
    control_unit = models.ForeignKey(
        'ControlUnit', on_delete=models.CASCADE, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Блок управления"),
        help_text=_("Тип БУ, для которого актуальна строка; null — строки "
                    "слота control_unit и профильные строки"),
    )
    power_supply = models.ForeignKey(
        'params.PowerSupplies', on_delete=models.CASCADE, null=True, blank=True,
        related_name='cu_matrix_rows',
        verbose_name=_("Напряжение питания"),
        help_text=_("Напряжение питания мотора; null — любое"),
    )
    signal_power = models.ForeignKey(
        'CuSignalPower', on_delete=models.PROTECT, null=True, blank=True,
        related_name='cu_matrix_rows',
        verbose_name=_("Схема цепей управления"),
        help_text=_("Схема цепей (источник × напряжение × полярность), при "
                    "которой действует строка; null — любая схема. Набор "
                    "сигналов дистанционного управления зависит от выбранной "
                    "схемы"),
    )
    mode = models.CharField(
        max_length=20, choices=CuMatrixMode.choices, default=CuMatrixMode.BOTH,
        verbose_name=_("Режим"),
        help_text=_("Режим работы, для которого актуальна строка"),
    )
    control_signal = models.ForeignKey(
        'CuControlSignal', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Командный сигнал"),
        help_text=_("Строка описывает входную команду"),
    )
    feedback_signal = models.ForeignKey(
        'CuFeedbackSignal', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Сигнал ОС"),
        help_text=_("Строка описывает выходной сигнал обратной связи"),
    )
    protocol = models.ForeignKey(
        'CuCommProtocol', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Протокол"),
        help_text=_("Строка описывает шину (только для слота PROTOCOL)"),
    )
    device = models.ForeignKey(
        'CuFeedbackDevice', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Устройство ОС"),
        help_text=_("Устройство, выдающее сигнал (только с feedback_signal; "
                    "device.emits должен содержать его)"),
    )
    heater_supply = models.ForeignKey(
        'CuHeaterSupply', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Питание обогрева"),
        help_text=_("Только для слота HEATER_CONTROL_UNIT"),
    )

    class Meta:
        verbose_name = _("Строка матрицы БУ")
        verbose_name_plural = _("Строки матрицы БУ")
        ordering = ['sorting_order', 'id']
        indexes = [
            models.Index(fields=['brand']),
            models.Index(fields=['model_line']),
            models.Index(fields=['body']),
            models.Index(fields=['model_line_item']),
            models.Index(fields=['control_unit', 'power_supply', 'mode']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(brand__isnull=False, model_line__isnull=True,
                             body__isnull=True, model_line_item__isnull=True)
                    | models.Q(brand__isnull=True, model_line__isnull=False,
                               body__isnull=True, model_line_item__isnull=True)
                    | models.Q(brand__isnull=True, model_line__isnull=True,
                               body__isnull=False, model_line_item__isnull=True)
                    | models.Q(brand__isnull=True, model_line__isnull=True,
                               body__isnull=True, model_line_item__isnull=False)
                    | models.Q(brand__isnull=True, model_line__isnull=True,
                               body__isnull=True, model_line_item__isnull=True)
                ),
                name='cu_matrix_scope_single'),
            models.CheckConstraint(
                check=(
                    models.Q(control_signal__isnull=False, feedback_signal__isnull=True,
                             protocol__isnull=True)
                    | models.Q(control_signal__isnull=True, feedback_signal__isnull=False,
                               protocol__isnull=True)
                    | models.Q(control_signal__isnull=True, feedback_signal__isnull=True,
                               protocol__isnull=False)
                    | models.Q(control_signal__isnull=True, feedback_signal__isnull=True,
                               protocol__isnull=True)
                ),
                name='cu_matrix_signal_single'),
        ]

    def _base_name(self, locale=None):
        """Имя строки из полезной нагрузки; иначе своё name/имя слота."""
        if self.name:
            return pick_i18n(self.name_i18n, locale, fallback=self.name)
        if self.option_id:
            return localized_name(self.option, locale)
        if self.feedback_signal_id:
            return localized_name(self.feedback_signal, locale)
        if self.control_signal_id:
            return localized_name(self.control_signal, locale)
        if self.protocol_id:
            return localized_name(self.protocol, locale)
        if self.heater_supply_id:
            return localized_name(self.heater_supply, locale)
        if self.control_unit_id:
            return localized_name(self.control_unit, locale)
        return localized_name(self.slot, locale)

    def clean(self):
        super().clean()
        if self.option_id and self.option.slot_id != self.slot_id:
            raise ValidationError(
                {'option': _('Опция принадлежит другому слоту.')})
        if self.protocol_id and self.slot.code != 'PROTOCOL':
            raise ValidationError(
                {'protocol': _('Протокол заполняется только для строк слота '
                               'PROTOCOL.')})
        if self.heater_supply_id and self.slot.code != 'HEATER_CONTROL_UNIT':
            raise ValidationError(
                {'heater_supply': _('Питание обогрева — только для слота '
                                    'HEATER_CONTROL_UNIT.')})
        if (self.device_id and not self.feedback_signal_id
                and not self.name):
            raise ValidationError(
                {'device': _('Устройство ОС задаётся только вместе с сигналом '
                             'ОС (или на none-строке с названием).')})
        if (self.device_id and self.feedback_signal_id
                and not self.device.emits.filter(pk=self.feedback_signal_id).exists()):
            raise ValidationError(
                {'device': _('Устройство не выдаёт указанный сигнал ОС.')})


class CuSlotRule(LocalizedDictFieldsMixin, AbstractSlotRule):
    """Правило динамики конфигуратора БУ (Паттерн В).

    Зачем: «если значение слота-условия [оператор] значение → действие над
    слотом-целью» (показать/скрыть/заблокировать/обязать/дефолт). Заменяет
    хардкод: профиль БУ → слоты, HART ↔ SETPOINT, скрытие обогрева для
    kind=NONE и т.п.

    Добавлено относительно AbstractSlotRule:

    - ``when_slot``/``target_slot`` — FK на слоты;
    - ``evaluate(current_value)`` — сравнение по when_operator (отладочный
      словарь; финальный выравнивается с фильтрами/требованиями).
    """
    when_slot = models.ForeignKey(
        CuSlot, on_delete=models.CASCADE,
        related_name='rules_when',
        verbose_name=_("Слот-условие"),
        help_text=_("Значение этого слота сравнивается с when_value"),
    )
    target_slot = models.ForeignKey(
        CuSlot, on_delete=models.CASCADE,
        related_name='rules_target',
        verbose_name=_("Слот-действие"),
        help_text=_("Слот, к которому применяется action"),
    )

    class Meta:
        verbose_name = _("Правило конфигуратора БУ")
        verbose_name_plural = _("Правила конфигуратора БУ")
        ordering = ['-priority', 'id']

    def evaluate(self, current_value):
        """Сравнить значение слота-условия с when_value.

        ``current_value`` — выбранное значение when-слота (строка/число/
        список). Возвращает True, если условие выполнено.
        """
        op = self.when_operator
        expected = self.when_value
        if op == 'is_set':
            return current_value not in (None, '', [])
        if op == 'not_exact':
            return current_value != expected
        if op == 'icontains':
            return expected is not None and str(expected) in str(current_value or '')
        if op == 'gte':
            try:
                return float(current_value) >= float(expected)
            except (TypeError, ValueError):
                return False
        if op == 'lte':
            try:
                return float(current_value) <= float(expected)
            except (TypeError, ValueError):
                return False
        if op == 'in':
            return expected is not None and current_value in expected
        if op == 'not_in':
            return expected is not None and current_value not in expected
        return current_value == expected
