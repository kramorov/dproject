# ea_control/models/dictionaries.py
"""
Справочники физики БУ — копии справочников ЭП (изоляция от electric_actuators).

Зачем копии: ea_control отлаживается как самостоятельная сущность, не
затрагивая рабочие модели ЭП (slots.md → «План: отладка паттерна…», Фаза 2).
После отладки решится судьба оригиналов (слияние/замена). Коды записей
**сохраняются как в оригинале** — они ключи маппинга при миграции данных.

Состав:

- ``CuSignalForm`` ← EaSignalForm — электрические формы сигналов;
- ``CuControlSignal`` ← EaControlSignal — входные команды БУ;
- ``CuFeedbackSignal`` ← EaFeedbackSignal — выходные сигналы ОС;
- ``CuCommProtocol`` ← EaCommProtocol — шинные протоколы;
- ``CuFeedbackDevice`` ← EaFeedbackDevice — устройства ОС (датчики);
- ``CuHeaterSupply`` ← params.ActuatorHeaterSupply — питание обогрева;
- ``CuLocationOption`` ← params.ControlUnitLocationOption — место установки БУ;
- ``CuCapability`` — новое: функции БУ, не являющиеся сигналами (PST,
  datalogger, Bluetooth, ESD, PID, interrupter timer…).

Локализация: ``name``/``description`` — ru-поля для админки; переводы сайта —
``name_i18n``/``description_i18n`` (LocalizedDictFieldsMixin). Коды и
аббревиатуры не переводятся.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import (CopyMixin, LocalizedDictFieldsMixin,
                                 OptionListToSelectMixin)


class CuSignalFormCategory(models.TextChoices):
    """Категория электрической формы сигнала."""
    CONTACT = 'contact', _('Сухой контакт')
    ANALOG = 'analog', _('Аналоговый (токовая петля)')
    DISCRETE = 'discrete', _('Дискретная команда (напряжение)')
    RESISTANCE = 'resistance', _('Сопротивление (потенциометр)')


class CuSignalForm(CopyMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Электрическая форма сигнала БУ (копия EaSignalForm).

    Зачем: физика клемм — в какой форме сигнал существует (сухой контакт,
    петля 4–20 мА, дискретная команда, потенциометр). Расширяется данными
    (записи, не миграции). На форму ссылаются CuControlSignal/CuFeedbackSignal
    и валидации «категория сигнала × категория формы».

    Поля: code (ключ маппинга), name, category (contact/analog/discrete/
    resistance), description, sorting_order, is_active.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код формы, например «DRY_SPDT», «AN_4_20_PASSIVE»"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название формы, например «Сухой контакт SPDT»"),
    )
    category = models.CharField(
        max_length=20, choices=CuSignalFormCategory.choices,
        verbose_name=_("Категория"),
        help_text=_("Категория формы: контакт / аналог / дискретная команда / "
                    "сопротивление"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение формы: схема подключения, полярность, особенности"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Форма сигнала БУ")
        verbose_name_plural = _("Формы сигналов БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class CuControlSignalRole(models.TextChoices):
    """Смысловые роли входных (управляющих) сигналов."""
    CMD_OCS = 'CMD_OCS', _('Команда Открыть/Стоп/Закрыть')
    CMD_REMOTE = 'CMD_REMOTE', _('Команда дистанционного управления')
    CMD_LOCK = 'CMD_LOCK', _('Блокировка')
    CMD_MANUAL_OVERRIDE = 'CMD_MANUAL_OVERRIDE', _('Ручное дублирование')
    CMD_4_20MA = 'CMD_4_20MA', _('Уставка положения 4–20 мА')
    CMD_0_10V = 'CMD_0_10V', _('Уставка положения 0–10 В')
    CMD_EMERGENCY_OPEN = 'CMD_EMERGENCY_OPEN', _('Аварийная команда «Открыть»')
    CMD_EMERGENCY_CLOSE = 'CMD_EMERGENCY_CLOSE', _('Аварийная команда «Закрыть»')
    MODE = 'MODE', _('Переключение режима open-close ↔ modulating')
    INTERLOCK_OPEN = 'INTERLOCK_OPEN', _('Блокировка «Открыть» (interlock)')
    INTERLOCK_CLOSE = 'INTERLOCK_CLOSE', _('Блокировка «Закрыть» (interlock)')
    DRIVE_ENABLE = 'DRIVE_ENABLE', _('Разрешение хода (drive enable)')


class _Analog4to20Mixin:
    """Общая валидация для сигналов с петлёй 4–20 мА и HART."""

    def validate_analog_fields(self, form, hart):
        """HART допустим только на аналоговой петле (категория формы analog)."""
        if hart and form and form.category != 'analog':
            raise ValidationError(
                {'hart': _('HART допустим только для аналоговых форм 4–20 мА.')})


class CuControlSignal(_Analog4to20Mixin, CopyMixin, LocalizedDictFieldsMixin,
                      OptionListToSelectMixin):
    """Входной (управляющий) сигнал БУ (копия EaControlSignal).

    Зачем: физика входных клемм БУ — какие команды он принимает и в какой
    форме. Одна запись = один канал команды. ``voltage``/``current`` —
    параметры входа БУ (что он ожидает на клемме), а не коммутируемая
    способность.

    Поля: role (смысловая роль команды), category (discrete/analog),
    form (FK CuSignalForm), voltage, current, wires, hart, code (ключ
    маппинга), name, description, sorting_order, is_active.
    """
    role = models.CharField(
        max_length=40, choices=CuControlSignalRole.choices,
        verbose_name=_("Роль"),
        help_text=_("Смысловая роль команды: О/С/З, уставка, ESD, блокировка…"),
    )
    category = models.CharField(
        max_length=20,
        choices=(('discrete', _('Дискретный')), ('analog', _('Аналоговый'))),
        verbose_name=_("Категория"),
        help_text=_("Дискретная команда или аналоговая уставка"),
    )
    form = models.ForeignKey(
        CuSignalForm, on_delete=models.PROTECT,
        related_name='control_signals',
        verbose_name=_("Форма"),
        help_text=_("Электрическая форма на клеммах (DISC_AC/DISC_DC/AN_4_20_*)"),
    )
    voltage = models.DecimalField(
        max_digits=7, decimal_places=1, null=True, blank=True,
        verbose_name=_("Напряжение входа, В"),
        help_text=_("Номинал цепи команды (для discrete); null для analog"),
    )
    current = models.DecimalField(
        max_digits=7, decimal_places=1, null=True, blank=True,
        verbose_name=_("Ток входа, мА"),
        help_text=_("Потребление цепи входа, мА"),
    )
    wires = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("Проводов на канал"),
        help_text=_("Число проводов/клемм канала — данные для генератора схем"),
    )
    hart = models.BooleanField(
        default=False,
        verbose_name=_("HART"),
        help_text=_("HART поверх петли 4–20 мА (только для форм AN_4_20_*)"),
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код сигнала, например «CMD_OCS_220AC»"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название, например «Команда О/С/З 220 В AC»"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение: полярность, контроль обрыва, примечания"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Командный сигнал БУ")
        verbose_name_plural = _("Командные сигналы БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.validate_analog_fields(self.form, self.hart)
        if self.category == 'discrete' and self.form.category not in (
                'discrete', 'contact'):
            raise ValidationError(
                {'form': _('Для дискретной команды нужна форма DISC_*/контакт.')})
        if self.category == 'analog' and self.form.category != 'analog':
            raise ValidationError(
                {'form': _('Для аналоговой уставки нужна форма AN_4_20_*.')})


class CuFeedbackSignalRole(models.TextChoices):
    """Смысловые роли выходных сигналов обратной связи."""
    END_OPEN = 'END_OPEN', _('Конечное положение «Открыто»')
    END_CLOSE = 'END_CLOSE', _('Конечное положение «Закрыто»')
    WAY_OPEN = 'WAY_OPEN', _('Промежуточное положение (открытие)')
    WAY_CLOSE = 'WAY_CLOSE', _('Промежуточное положение (закрытие)')
    TORQUE_OPEN = 'TORQUE_OPEN', _('Моментный выключатель «Открыто»')
    TORQUE_CLOSE = 'TORQUE_CLOSE', _('Моментный выключатель «Закрыто»')
    POSITION = 'POSITION', _('Текущее положение (аналоговая ОС)')
    OVERHEAT = 'OVERHEAT', _('Перегрев электродвигателя')
    TURN_COUNTER = 'TURN_COUNTER', _('Счётчик оборотов')
    ALARM = 'ALARM', _('Авария')
    READY = 'READY', _('Готовность')
    TORQUE_ANALOG = 'TORQUE_ANALOG', _('Аналоговый момент')
    STOP = 'STOP', _('Останов (привод не в работе)')
    LOCAL_REMOTE = 'LOCAL_REMOTE', _('Режим местное/удалённое управление')
    SELECTOR_POSITION = 'SELECTOR_POSITION', _('Положение ключа-селектора')
    PHASE_LOSS = 'PHASE_LOSS', _('Авария: потеря фазы')


class CuContactNormal(models.TextChoices):
    """Нормальное состояние контакта (для выходных контактных сигналов)."""
    NO = 'NO', _('Нормально-разомкнутый (NO)')
    NC = 'NC', _('Нормально-замкнутый (NC)')
    CHANGEOVER = 'CHANGEOVER', _('Перекидной (переключающий)')


class CuFeedbackSignal(_Analog4to20Mixin, CopyMixin, LocalizedDictFieldsMixin,
                       OptionListToSelectMixin):
    """Выходной сигнал обратной связи БУ (копия EaFeedbackSignal).

    Зачем: физика выходных клемм БУ — что он выдаёт наружу (концевые/путевые/
    моментные контакты, позиция, перегрев, авария…). Одна запись = один канал
    ОС. Для контактов ``max_voltage``/``max_current`` — коммутируемая
    способность; для потенциометра — ``resistance_kohm``/``max_power_w``/
    ``turns``; для петли — активность уже в форме.

    Поля: role, category (contact/analog), form (FK CuSignalForm),
    max_voltage, max_current, contact_normal, resistance_kohm, max_power_w,
    turns, wires, hart, code (ключ маппинга), name, description,
    sorting_order, is_active.
    """
    role = models.CharField(
        max_length=40, choices=CuFeedbackSignalRole.choices,
        verbose_name=_("Роль"),
        help_text=_("Смысловая роль: концевые/путевые/моментные, позиция, авария…"),
    )
    category = models.CharField(
        max_length=20,
        choices=(('contact', _('Контакт')), ('analog', _('Аналоговый'))),
        verbose_name=_("Категория"),
        help_text=_("Контакт (сухой) или аналоговый выход"),
    )
    form = models.ForeignKey(
        CuSignalForm, on_delete=models.PROTECT,
        related_name='feedback_signals',
        verbose_name=_("Форма"),
        help_text=_("Электрическая форма на клеммах "
                    "(DRY_*/AN_4_20_*/RES_POTENTIOMETER)"),
    )
    max_voltage = models.DecimalField(
        max_digits=7, decimal_places=1, null=True, blank=True,
        verbose_name=_("Макс. коммутируемое напряжение, В"),
        help_text=_("Для контактов; null для аналоговых форм"),
    )
    max_current = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name=_("Макс. коммутируемый ток, А"),
        help_text=_("Для контактов; null для аналоговых форм"),
    )
    contact_normal = models.CharField(
        max_length=10, choices=CuContactNormal.choices, null=True, blank=True,
        verbose_name=_("Нормальное состояние контакта"),
        help_text=_("NO/NC/перекидной — для контактных форм; null иначе"),
    )
    resistance_kohm = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name=_("Сопротивление, кОм"),
        help_text=_("Полное сопротивление потенциометра (для RES_POTENTIOMETER)"),
    )
    max_power_w = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name=_("Мощность, Вт"),
        help_text=_("Допустимая мощность потенциометра (для RES_POTENTIOMETER)"),
    )
    turns = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("Обороты"),
        help_text=_("Число оборотов потенциометра полного хода; null иначе"),
    )
    wires = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("Проводов на канал"),
        help_text=_("Число проводов/клемм канала — данные для генератора схем"),
    )
    hart = models.BooleanField(
        default=False,
        verbose_name=_("HART"),
        help_text=_("HART поверх петли 4–20 мА (только для форм AN_4_20_*)"),
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код сигнала, например «FB_POS_4_20MA_ACTIVE»"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название, например «Позиция 4–20 мА, активный»"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение: нагрузочная способность, примечания"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Сигнал ОС БУ")
        verbose_name_plural = _("Сигналы ОС БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.validate_analog_fields(self.form, self.hart)
        if self.category == 'contact' and self.form.category != 'contact':
            raise ValidationError(
                {'form': _('Для контакта нужна форма DRY_*.')})
        if self.category != 'contact' and self.contact_normal:
            raise ValidationError(
                {'contact_normal': _('Нормальное состояние контакта задаётся '
                                     'только для контактных сигналов.')})
        if self.category == 'analog' and self.form.category not in (
                'analog', 'resistance'):
            raise ValidationError(
                {'form': _('Для аналогового сигнала нужна форма AN_4_20_* или '
                           'RES_POTENTIOMETER.')})
        if self.form.category == 'resistance' and not self.resistance_kohm:
            raise ValidationError(
                {'resistance_kohm': _('Для потенциометра обязательно '
                                      'сопротивление.')})


class CuProtocolTransport(models.TextChoices):
    """Физический транспорт шины."""
    RS485 = 'RS485', _('RS-485')
    ETHERNET = 'ETHERNET', _('Ethernet')
    OTHER = 'OTHER', _('Прочее')


class CuCommProtocol(CopyMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Шинный протокол связи БУ (копия EaCommProtocol).

    Зачем: физика шины — какие протоколы поддерживает БУ (Modbus RTU/TCP,
    PROFIBUS DP, PROFINET, Foundation Fieldbus…). HART сюда не входит — это
    атрибут сигнала петли 4–20 мА.

    Поля: code (ключ маппинга), name, transport, description, sorting_order,
    is_active.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код протокола, например «MODBUS_RTU»"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название протокола, например «Modbus RTU»"),
    )
    transport = models.CharField(
        max_length=20, choices=CuProtocolTransport.choices,
        verbose_name=_("Транспорт"),
        help_text=_("Физический транспорт шины (RS-485, Ethernet, …)"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Краткая характеристика канала (скорость, топология, "
                    "примечания)"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Протокол связи БУ")
        verbose_name_plural = _("Протоколы связи БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class CuFeedbackDeviceKind(models.TextChoices):
    """Категория устройства ОС: позиционный датчик или теплозащита."""
    POSITION_SENSOR = 'POSITION_SENSOR', _('Датчик положения')
    THERMAL_SENSOR = 'THERMAL_SENSOR', _('Датчик температуры (теплозащита)')


class CuFeedbackTechnology(models.TextChoices):
    """Технология датчика."""
    POTENTIOMETER = 'POTENTIOMETER', _('Потенциометрический')
    MWG = 'MWG', _('Магнитно-волновой (MWG)')
    ELECTRONIC = 'ELECTRONIC', _('Электронный')


class CuFeedbackDevice(CopyMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Устройство обратной связи (копия EaFeedbackDevice).

    Зачем: физика датчиков — что за устройство выдаёт сигнал ОС (потенциометр,
    MWG, термореле). Сигнал описывает клеммы, устройство — сам датчик;
    ``emits`` связывает их (устройство выдаёт конкретные сигналы — валидация
    матрицы).

    Поля: code (ключ маппинга), kind (POSITION_SENSOR/THERMAL_SENSOR), name,
    technology, contactless, emits (M2M CuFeedbackSignal), equivalents
    (M2M self), accuracy, life_cycles, temp_range, description,
    sorting_order, is_active.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код устройства, например «POT_1K»"),
    )
    kind = models.CharField(
        max_length=20, choices=CuFeedbackDeviceKind.choices,
        verbose_name=_("Категория"),
        help_text=_("Датчик положения или датчик температуры (теплозащита)"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название устройства, например «Потенциометр 1 кОм»"),
    )
    technology = models.CharField(
        max_length=20, choices=CuFeedbackTechnology.choices,
        verbose_name=_("Технология"),
        help_text=_("Потенциометрический / магнитно-волновой / электронный"),
    )
    contactless = models.BooleanField(
        default=False,
        verbose_name=_("Бесконтактный"),
        help_text=_("Датчик без механического контакта (MWG и т.п.)"),
    )
    emits = models.ManyToManyField(
        CuFeedbackSignal, blank=True,
        related_name='devices',
        verbose_name=_("Выдаёт сигналы"),
        help_text=_("Какие сигналы ОС выдаёт устройство"),
    )
    equivalents = models.ManyToManyField(
        'self', blank=True, symmetrical=True,
        verbose_name=_("Эквиваленты"),
        help_text=_("Взаимозаменяемые устройства"),
    )
    accuracy = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Точность"),
    )
    life_cycles = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Ресурс, циклов"),
    )
    temp_range = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Рабочая температура"),
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Устройство ОС БУ")
        verbose_name_plural = _("Устройства ОС БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class CuHeaterSupply(LocalizedDictFieldsMixin):
    """Питание антиконденсатного обогрева (копия params.ActuatorHeaterSupply).

    Зачем: варианты питания обогрева БУ/привода — от цепей питания, отдельная
    линия, нет. Используется опциями слота HEATER_CONTROL_UNIT.

    Поля: name, code (ключ маппинга, напр. «MOTOR_CIRCUIT»), electrical_specs,
    description, sorting_order, is_active.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Например: «От цепей питания устройства»"),
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например «MOTOR_CIRCUIT»"),
    )
    electrical_specs = models.CharField(
        max_length=255, blank=True,
        verbose_name=_("Электрические характеристики"),
        help_text=_("Например: «230В AC, 10 Вт» или «24В DC, 5 Вт»"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Примечания к варианту питания обогрева"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Питание обогрева БУ")
        verbose_name_plural = _("Питания обогрева БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class CuLocationOption(LocalizedDictFieldsMixin):
    """Место установки БУ (копия params.ControlUnitLocationOption).

    Зачем: где размещается блок управления на приводе (встроен, навесной,
    отдельный шкаф…). Ссылается с ControlUnit.location.

    Поля: name, code (ключ маппинга), description, sorting_order, is_active.
    """
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    code = models.CharField(max_length=50, verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Место размещения БУ")
        verbose_name_plural = _("Места размещения БУ")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class CuCapability(LocalizedDictFieldsMixin, CopyMixin, OptionListToSelectMixin):
    """Функция БУ, не являющаяся сигналом (новая модель).

    Зачем: «набор дополнительных возможностей» типа БУ — функции, которые не
    сводятся к клеммному сигналу: PST (partial stroke test), datalogger,
    Bluetooth, ESD, PID-регулятор, interrupter timer, местное управление.
    Выбор справочника+M2M, а не JSON: типобезопасность (опечатка кода
    невозможна), i18n имён, ссылки из правил/фильтров (slots.md, вопрос 5).
    Функции, покрытые слотами (INDICATOR/TURN_COUNTER/HEATER_*), сюда не
    дублируются.

    Поля: code, name, description, sorting_order, is_active.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код функции: PST, DATALOGGER, BLUETOOTH, ESD, "
                    "PID, INTERRUPTER_TIMER, LOCAL_CONTROL…"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название функции, например «Частичный ход (PST)»"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Что делает функция и в каких БУ встречается"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Функция БУ")
        verbose_name_plural = _("Функции БУ")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name
