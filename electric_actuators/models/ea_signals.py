# electric_actuators/models/ea_signals.py
"""
Каталоги сигналов электроприводов: входные команды и выходная обратная связь.

``EaControlSignal`` — входные (управляющие) сигналы, однонаправленные команды
приводу: OPEN/CLOSE/STOP, аварийные, уставка 4–20 мА, блокировки. Поля
``voltage``/``current`` описывают параметры ВХОДА БУ (что он ожидает на клемме).

``EaFeedbackSignal`` — выходные сигналы обратной связи (от привода наружу):
концевые/путевые/моментные контакты, позиция (4–20 мА или потенциометр),
перегрев, авария, готовность, аналоговый момент. Поля ``max_voltage``/
``max_current`` — коммутируемая способность контакта (какую нагрузку он может
замкнуть); для потенциометра — ``resistance_kohm``/``max_power_w``.

Физика датчиков не моделируется здесь (см. ``EaFeedbackDevice``) — сигнал
описывает только клеммы: форма + электрические параметры + число проводов.

``wires`` — число проводов/клемм канала: данные для генератора схем
подключения (фаза 8 плана).

``hart`` — признак HART поверх петли 4–20 мА (допустим только для форм
AN_4_20_*): HART не выбирается отдельно от петли, поэтому это атрибут сигнала,
а не запись ``EaCommProtocol``.

Локализация: ru-базовые поля + ``_i18n``-переводы (LocalizedDictFieldsMixin);
коды/аббревиатуры не переводятся.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import (CopyMixin, LocalizedDictFieldsMixin,
                                 OptionListToSelectMixin)


class EaControlSignalRole(models.TextChoices):
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


class EaFeedbackSignalRole(models.TextChoices):
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


class _Analog4to20Mixin:
    """Общая валидация для сигналов с петлёй 4–20 мА и HART."""

    def validate_analog_fields(self, form, hart):
        """HART допустим только на аналоговой петле (категория формы analog)."""
        if hart and form and form.category != 'analog':
            raise ValidationError(
                {'hart': _('HART допустим только для аналоговых форм 4–20 мА.')})


class EaContactNormal(models.TextChoices):
    """Нормальное состояние контакта (для выходных контактных сигналов)."""
    NO = 'NO', _('Нормально-разомкнутый (NO)')
    NC = 'NC', _('Нормально-замкнутый (NC)')
    CHANGEOVER = 'CHANGEOVER', _('Перекидной (переключающий)')


class EaControlSignal(_Analog4to20Mixin, CopyMixin, LocalizedDictFieldsMixin,
                      OptionListToSelectMixin):
    """Входной (управляющий) сигнал БУ электропривода.

    Одна запись = один канал команды. ``voltage``/``current`` — параметры входа
    БУ (что он ожидает на клемме), а не коммутируемая способность.
    """
    role = models.CharField(
        max_length=40, choices=EaControlSignalRole.choices,
        verbose_name=_("Роль"),
        help_text=_("Смысловая роль команды: О/С/З, уставка, ESD, блокировка…")
    )
    category = models.CharField(
        max_length=20,
        choices=(('discrete', _('Дискретный')), ('analog', _('Аналоговый'))),
        verbose_name=_("Категория"),
        help_text=_("Дискретная команда или аналоговая уставка")
    )
    form = models.ForeignKey(
        'EaSignalForm', on_delete=models.PROTECT,
        related_name='control_signals',
        verbose_name=_("Форма"),
        help_text=_("Электрическая форма на клеммах (DISC_AC/DISC_DC/AN_4_20_*)")
    )
    voltage = models.DecimalField(
        max_digits=7, decimal_places=1, null=True, blank=True,
        verbose_name=_("Напряжение входа, В"),
        help_text=_("Номинал цепи команды (для discrete); null для analog")
    )
    current = models.DecimalField(
        max_digits=7, decimal_places=1, null=True, blank=True,
        verbose_name=_("Ток входа, мА"),
        help_text=_("Потребление цепи входа, мА")
    )
    wires = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("Проводов на канал"),
        help_text=_("Число проводов/клемм канала — данные для генератора схем")
    )
    hart = models.BooleanField(
        default=False,
        verbose_name=_("HART"),
        help_text=_("HART поверх петли 4–20 мА (только для форм AN_4_20_*)")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код сигнала, например «CMD_OCS_220AC»")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название, например «Команда О/С/З 220 В AC»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение: полярность, контроль обрыва, примечания")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Командный сигнал ЭП")
        verbose_name_plural = _("Командные сигналы ЭП")
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


class EaFeedbackSignal(_Analog4to20Mixin, CopyMixin, LocalizedDictFieldsMixin,
                       OptionListToSelectMixin):
    """Выходной сигнал обратной связи БУ электропривода.

    Одна запись = один канал ОС. Для контактов ``max_voltage``/``max_current`` —
    коммутируемая способность; для потенциометра — ``resistance_kohm``/
    ``max_power_w``/``turns``; для петли — признак active/passive уже в форме.
    """
    role = models.CharField(
        max_length=40, choices=EaFeedbackSignalRole.choices,
        verbose_name=_("Роль"),
        help_text=_("Смысловая роль: концевые/путевые/моментные, позиция, авария…")
    )
    category = models.CharField(
        max_length=20,
        choices=(('contact', _('Контакт')), ('analog', _('Аналоговый'))),
        verbose_name=_("Категория"),
        help_text=_("Контакт (сухой) или аналоговый выход")
    )
    form = models.ForeignKey(
        'EaSignalForm', on_delete=models.PROTECT,
        related_name='feedback_signals',
        verbose_name=_("Форма"),
        help_text=_("Электрическая форма на клеммах (DRY_*/AN_4_20_*/RES_POTENTIOMETER)")
    )
    max_voltage = models.DecimalField(
        max_digits=7, decimal_places=1, null=True, blank=True,
        verbose_name=_("Макс. коммутируемое напряжение, В"),
        help_text=_("Для контактов; null для аналоговых форм")
    )
    max_current = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name=_("Макс. коммутируемый ток, А"),
        help_text=_("Для контактов; null для аналоговых форм")
    )
    contact_normal = models.CharField(
        max_length=10, choices=EaContactNormal.choices, null=True, blank=True,
        verbose_name=_("Нормальное состояние контакта"),
        help_text=_("NO/NC/перекидной — для контактных форм; null иначе")
    )
    resistance_kohm = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name=_("Сопротивление, кОм"),
        help_text=_("Полное сопротивление потенциометра (для RES_POTENTIOMETER)")
    )
    max_power_w = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name=_("Мощность, Вт"),
        help_text=_("Допустимая мощность потенциометра (для RES_POTENTIOMETER)")
    )
    turns = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("Обороты"),
        help_text=_("Число оборотов потенциометра полного хода; null иначе")
    )
    wires = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("Проводов на канал"),
        help_text=_("Число проводов/клемм канала — данные для генератора схем")
    )
    hart = models.BooleanField(
        default=False,
        verbose_name=_("HART"),
        help_text=_("HART поверх петли 4–20 мА (только для форм AN_4_20_*)")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код сигнала, например «FB_POS_4_20MA_ACTIVE»")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название, например «Позиция 4–20 мА, активный»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение: нагрузочная способность, примечания")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Сигнал ОС ЭП")
        verbose_name_plural = _("Сигналы ОС ЭП")
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
                {'contact_normal': _('Нормальное состояние контакта задаётся только для контактных сигналов.')})
        if self.category == 'analog' and self.form.category not in ('analog', 'resistance'):
            raise ValidationError(
                {'form': _('Для аналогового сигнала нужна форма AN_4_20_* или RES_POTENTIOMETER.')})
        if self.form.category == 'resistance' and not self.resistance_kohm:
            raise ValidationError(
                {'resistance_kohm': _('Для потенциометра обязательно сопротивление.')})
