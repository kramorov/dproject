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


CONTROL_SIGNAL_ROLES = (
    ('CMD_OCS', 'Команда Открыть/Стоп/Закрыть'),
    ('CMD_REMOTE', 'Команда дистанционного управления'),
    ('CMD_LOCK', 'Блокировка'),
    ('CMD_MANUAL_OVERRIDE', 'Ручное дублирование'),
    ('CMD_4_20MA', 'Уставка положения 4–20 мА'),
    ('CMD_0_10V', 'Уставка положения 0–10 В'),
    ('CMD_EMERGENCY_OPEN', 'Аварийная команда «Открыть»'),
    ('CMD_EMERGENCY_CLOSE', 'Аварийная команда «Закрыть»'),
    ('MODE', 'Переключение режима open-close ↔ modulating'),
    ('INTERLOCK_OPEN', 'Блокировка «Открыть» (interlock)'),
    ('INTERLOCK_CLOSE', 'Блокировка «Закрыть» (interlock)'),
    ('DRIVE_ENABLE', 'Разрешение хода (drive enable)'),
)

FEEDBACK_SIGNAL_ROLES = (
    ('END_OPEN', 'Конечное положение «Открыто»'),
    ('END_CLOSE', 'Конечное положение «Закрыто»'),
    ('WAY_OPEN', 'Промежуточное положение (открытие)'),
    ('WAY_CLOSE', 'Промежуточное положение (закрытие)'),
    ('TORQUE_OPEN', 'Моментный выключатель «Открыто»'),
    ('TORQUE_CLOSE', 'Моментный выключатель «Закрыто»'),
    ('POSITION', 'Текущее положение (аналоговая ОС)'),
    ('OVERHEAT', 'Перегрев электродвигателя'),
    ('TURN_COUNTER', 'Счётчик оборотов'),
    ('ALARM', 'Авария'),
    ('READY', 'Готовность'),
    ('TORQUE_ANALOG', 'Аналоговый момент'),
    ('STOP', 'Останов (привод не в работе)'),
    ('LOCAL_REMOTE', 'Режим местное/удалённое управление'),
    ('SELECTOR_POSITION', 'Положение ключа-селектора'),
    ('PHASE_LOSS', 'Авария: потеря фазы'),
)

CONTACT_NORMALS = (
    ('NO', 'Нормально-разомкнутый (NO)'),
    ('NC', 'Нормально-замкнутый (NC)'),
    ('CHANGEOVER', 'Перекидной (переключающий)'),
)


class EaControlSignalRole(CopyMixin, LocalizedDictFieldsMixin,
                          OptionListToSelectMixin):
    """Смысловая роль входного (управляющего) сигнала.

    Раньше была ``models.TextChoices`` — заменена на справочную модель;
    общая для ЭП и БУ.
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Роль командного сигнала")
        verbose_name_plural = _("Роли командных сигналов")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class EaFeedbackSignalRole(CopyMixin, LocalizedDictFieldsMixin,
                           OptionListToSelectMixin):
    """Смысловая роль выходного сигнала обратной связи (справочник).

    Раньше была ``models.TextChoices`` — заменена на справочную модель;
    общая для ЭП и БУ.
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Роль сигнала ОС")
        verbose_name_plural = _("Роли сигналов ОС")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class _Analog4to20Mixin:
    """Общая валидация для сигналов с петлёй 4–20 мА и HART."""

    def validate_analog_fields(self, form, hart):
        """HART допустим только на аналоговой петле (категория формы analog)."""
        if hart and form and form.category.code != 'analog':
            raise ValidationError(
                {'hart': _('HART допустим только для аналоговых форм 4–20 мА.')})


class EaContactNormal(CopyMixin, LocalizedDictFieldsMixin,
                      OptionListToSelectMixin):
    """Нормальное состояние контакта (для выходных контактных сигналов).

    Раньше была ``models.TextChoices`` — заменена на справочную модель;
    общая для ЭП и БУ.
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Нормальное состояние контакта")
        verbose_name_plural = _("Нормальные состояния контактов")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class EaControlSignal(_Analog4to20Mixin, CopyMixin, LocalizedDictFieldsMixin,
                      OptionListToSelectMixin):
    """Входной (управляющий) сигнал БУ электропривода.

    Одна запись = один канал команды. ``voltage``/``current`` — параметры входа
    БУ (что он ожидает на клемме), а не коммутируемая способность.
    """
    role = models.ForeignKey(
        EaControlSignalRole, on_delete=models.PROTECT,
        related_name='control_signals',
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
        if self.category == 'discrete' and self.form.category.code not in (
                'discrete', 'contact'):
            raise ValidationError(
                {'form': _('Для дискретной команды нужна форма DISC_*/контакт.')})
        if self.category == 'analog' and self.form.category.code != 'analog':
            raise ValidationError(
                {'form': _('Для аналоговой уставки нужна форма AN_4_20_*.')})


class EaFeedbackSignal(_Analog4to20Mixin, CopyMixin, LocalizedDictFieldsMixin,
                       OptionListToSelectMixin):
    """Выходной сигнал обратной связи БУ электропривода.

    Одна запись = один канал ОС. Для контактов ``max_voltage``/``max_current`` —
    коммутируемая способность; для потенциометра — ``resistance_kohm``/
    ``max_power_w``/``turns``; для петли — признак active/passive уже в форме.
    """
    role = models.ForeignKey(
        EaFeedbackSignalRole, on_delete=models.PROTECT,
        related_name='feedback_signals',
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
    contact_normal = models.ForeignKey(
        EaContactNormal, on_delete=models.PROTECT, null=True, blank=True,
        related_name='feedback_signals',
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
        if self.category == 'contact' and self.form.category.code != 'contact':
            raise ValidationError(
                {'form': _('Для контакта нужна форма DRY_*.')})
        if self.category != 'contact' and self.contact_normal:
            raise ValidationError(
                {'contact_normal': _('Нормальное состояние контакта задаётся только для контактных сигналов.')})
        if self.category == 'analog' and self.form.category.code not in ('analog', 'resistance'):
            raise ValidationError(
                {'form': _('Для аналогового сигнала нужна форма AN_4_20_* или RES_POTENTIOMETER.')})
        if self.form.category.code == 'resistance' and not self.resistance_kohm:
            raise ValidationError(
                {'resistance_kohm': _('Для потенциометра обязательно сопротивление.')})
