# electric_actuators/models/ea_signal_matrix.py
"""
Матрица доступности сигналов ЭП и привязки схем подключения (фаза 4).

``EaSignalMatrixEntry`` — наследуемая матрица доступности «БУ × напряжение ×
режим → опция». Строка ссылается на одну из трёх сущностей (командный сигнал /
сигнал ОС / протокол) либо является явной строкой «нет» (все три FK пустые —
например, «Без переключателей» для MWG-позиций, «Без обогрева»).

Правила:
- скоуп: ровно один из brand / model_line / model_line_item; специфичнее
  перекрывает общий (model_line_item → model_line → brand);
- слот (``EaSignalSlot``): single-choice группа; ``is_default`` — предвыбор;
- ``bundle``: строки с общим кодом пакета выбираются атомарно (MWG = три строки
  в трёх слотах); если хоть одна недоступна — пакет целиком недоступен;
- ``availability='na'`` на специфичном уровне ЗАПРЕЩАЕТ унаследованную строку;
- ``conflicts`` (M2M self): парные запреты одновременного выбора; составные
  (лимит клемм Q/M) — через ``configurator.ParameterRule`` (фаза 4 плана);
- ``heater_supply`` — только для слотов HEATER_ACTUATOR/HEATER_CONTROL_UNIT
  (NO_HEATER/SEPARATE_LINE/MOTOR_CIRCUIT из ``params.ActuatorHeaterSupply``);
- ``device`` — только с feedback_signal, и ``device.emits`` должен его содержать.

``EaWiringDiagramBinding`` — привязка схемы подключения (медиабиблиотека) к
набору выбранных строк: схема «есть или нет». ``match_type`` exact — выбор
должен совпасть с подписью, superset — подпись является подмножеством выбора.
Резолвинг схемы — в ``electric_actuators.services.ea_signal_resolver``.

Локализация: имя строки выводится как «значение справочника + суффикс
(Стандарт)/(Опция)» через ``localized_name(locale)`` (паттерн through-опций,
уроки 18–22 lang.md); суффикс не хранится в name_i18n.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, LocalizedDictFieldsMixin
from core.utils.localization import localized_name, pick_i18n


class EaAvailability(models.TextChoices):
    """Доступность опции в матрице."""
    STD = 'std', _('Стандарт')
    OPT = 'opt', _('Опция')
    NA = 'na', _('Недоступно')


class EaMatrixMode(models.TextChoices):
    """Режим работы, для которого актуальна строка."""
    ON_OFF = 'on_off', _('Двухпозиционный (on-off)')
    MODULATING = 'modulating', _('Модулирующий')
    BOTH = 'both', _('Оба режима')


class EaSignalMatrixEntry(CopyMixin, LocalizedDictFieldsMixin):
    """Строка матрицы доступности сигналов БУ электропривода."""
    brand = models.ForeignKey(
        'producers.Brands', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_signal_matrix_rows',
        verbose_name=_("Бренд"),
        help_text=_("Уровень скоупа «бренд» (матрица производителя целиком)")
    )
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_signal_matrix_rows',
        verbose_name=_("Серия"),
        help_text=_("Уровень скоупа «серия»")
    )
    body = models.ForeignKey(
        'ElectricActuatorBody', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_signal_matrix_rows',
        verbose_name=_("Корпус"),
        help_text=_("Уровень скоупа «корпус»: модели общего корпуса (в т.ч. QUI-варианты) "
                    "разделяют опции")
    )
    model_line_item = models.ForeignKey(
        'ElectricActuatorModelLineItem', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_signal_matrix_rows',
        verbose_name=_("Модель"),
        help_text=_("Уровень скоупа «модель» (самый специфичный)")
    )
    control_unit = models.ForeignKey(
        'params.ControlUnitInstalledOption', on_delete=models.CASCADE,
        related_name='ea_signal_matrix_rows',
        verbose_name=_("Блок управления"),
        help_text=_("Тип БУ, для которого актуальна строка")
    )
    power_supply = models.ForeignKey(
        'params.PowerSupplies', on_delete=models.CASCADE,
        related_name='ea_signal_matrix_rows',
        verbose_name=_("Напряжение питания"),
        help_text=_("Напряжение питания мотора")
    )
    mode = models.CharField(
        max_length=20, choices=EaMatrixMode.choices, default=EaMatrixMode.BOTH,
        verbose_name=_("Режим"),
        help_text=_("Режим работы, для которого актуальна строка")
    )
    slot = models.ForeignKey(
        'EaSignalSlot', on_delete=models.PROTECT,
        related_name='matrix_rows',
        verbose_name=_("Слот"),
        help_text=_("Группа взаимоисключающих опций (single-choice)")
    )
    bundle = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name=_("Пакет"),
        help_text=_("Код пакета: строки с общим bundle выбираются атомарно "
                    "(например MWG: три строки в трёх слотах)")
    )
    control_signal = models.ForeignKey(
        'EaControlSignal', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Командный сигнал"),
        help_text=_("Строка описывает входную команду")
    )
    feedback_signal = models.ForeignKey(
        'EaFeedbackSignal', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Сигнал ОС"),
        help_text=_("Строка описывает выходной сигнал обратной связи")
    )
    protocol = models.ForeignKey(
        'EaCommProtocol', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Протокол"),
        help_text=_("Строка описывает шину (только для слота PROTOCOL)")
    )
    device = models.ForeignKey(
        'EaFeedbackDevice', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Устройство ОС"),
        help_text=_("Устройство, выдающее сигнал (только с feedback_signal; "
                    "device.emits должен содержать его)")
    )
    heater_supply = models.ForeignKey(
        'params.ActuatorHeaterSupply', on_delete=models.PROTECT, null=True, blank=True,
        related_name='matrix_rows',
        verbose_name=_("Питание обогрева"),
        help_text=_("Только для слотов HEATER_ACTUATOR/HEATER_CONTROL_UNIT "
                    "(NO_HEATER/SEPARATE_LINE/MOTOR_CIRCUIT)")
    )
    availability = models.CharField(
        max_length=10, choices=EaAvailability.choices, default=EaAvailability.OPT,
        verbose_name=_("Доступность"),
        help_text=_("std — стандарт, opt — опция, na — запрет унаследованной строки")
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("По умолчанию"),
        help_text=_("Предвыбор в слоте (не более одной std/дефолтной строки на слот)")
    )
    encoding = models.CharField(
        max_length=50, blank=True,
        verbose_name=_("Кодировка"),
        help_text=_("Вклад в основной артикул")
    )
    ext_encoding = models.CharField(
        max_length=50, blank=True,
        verbose_name=_("Расширенная кодировка"),
        help_text=_("Вклад в ext-часть артикула (позиция кода заказа)")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Название"),
        help_text=_("Для none-строк («Без переключателей») и особых случаев; "
                    "иначе имя выводится из сигнала/устройства")
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    conflicts = models.ManyToManyField(
        'self', blank=True, symmetrical=True,
        verbose_name=_("Конфликты"),
        help_text=_("Парный запрет одновременного выбора (составные запреты — "
                    "через configurator.ParameterRule)")
    )

    class Meta:
        verbose_name = _("Строка матрицы сигналов ЭП")
        verbose_name_plural = _("Строки матрицы сигналов ЭП")
        ordering = ['sorting_order', 'id']
        indexes = [
            models.Index(fields=['brand']),
            models.Index(fields=['model_line']),
            models.Index(fields=['body']),
            models.Index(fields=['model_line_item']),
            models.Index(fields=['control_unit', 'power_supply', 'mode']),
        ]
        constraints = [
            # ровно один скоуп
            models.CheckConstraint(
                check=(
                    models.Q(brand__isnull=False, model_line__isnull=True, body__isnull=True, model_line_item__isnull=True)
                    | models.Q(brand__isnull=True, model_line__isnull=False, body__isnull=True, model_line_item__isnull=True)
                    | models.Q(brand__isnull=True, model_line__isnull=True, body__isnull=False, model_line_item__isnull=True)
                    | models.Q(brand__isnull=True, model_line__isnull=True, body__isnull=True, model_line_item__isnull=False)
                ),
                name='ea_matrix_scope_single'),
            # ровно один сигнал/протокол ЛИБО none-строка
            models.CheckConstraint(
                check=(
                    models.Q(control_signal__isnull=False, feedback_signal__isnull=True, protocol__isnull=True)
                    | models.Q(control_signal__isnull=True, feedback_signal__isnull=False, protocol__isnull=True)
                    | models.Q(control_signal__isnull=True, feedback_signal__isnull=True, protocol__isnull=False)
                    | models.Q(control_signal__isnull=True, feedback_signal__isnull=True, protocol__isnull=True)
                ),
                name='ea_matrix_signal_single'),
        ]

    def __str__(self):
        return self.name or self.localized_name()

    def _base_name(self, locale=None):
        """Базовое имя строки: своё name либо имя сигнала/устройства."""
        if self.name:
            return pick_i18n(self.name_i18n, locale, fallback=self.name)
        if self.feedback_signal_id:
            return localized_name(self.feedback_signal, locale)
        if self.control_signal_id:
            return localized_name(self.control_signal, locale)
        if self.protocol_id:
            return localized_name(self.protocol, locale)
        if self.heater_supply_id:
            return localized_name(self.heater_supply, locale)
        return str(self.slot)

    def localized_name(self, locale=None):
        """Имя + суффикс (Стандарт)/(Опция) — на лету, не хранится в name_i18n."""
        base = self._base_name(locale)
        if self.availability == EaAvailability.STD:
            return f'{base} ({_("Стандарт")})'
        if self.availability == EaAvailability.OPT:
            return f'{base} ({_("Опция")})'
        return base

    def clean(self):
        super().clean()
        if self.protocol_id and self.slot.code != 'PROTOCOL':
            raise ValidationError(
                {'protocol': _('Протокол заполняется только для строк слота PROTOCOL.')})
        if self.heater_supply_id and not self.slot.code.startswith('HEATER_'):
            raise ValidationError(
                {'heater_supply': _('Питание обогрева — только для слотов HEATER_*.')})
        if self.device_id and not self.feedback_signal_id:
            raise ValidationError(
                {'device': _('Устройство ОС задаётся только вместе с сигналом ОС.')})
        if (self.device_id and self.feedback_signal_id
                and not self.device.emits.filter(pk=self.feedback_signal_id).exists()):
            raise ValidationError(
                {'device': _('Устройство не выдаёт указанный сигнал ОС.')})


class EaDiagramMatchType(models.TextChoices):
    """Семантика совпадения подписи схемы с выбором."""
    EXACT = 'exact', _('Точное совпадение')
    SUPERSET = 'superset', _('Подпись — подмножество выбора')


class EaWiringDiagramBinding(CopyMixin, LocalizedDictFieldsMixin):
    """Привязка схемы подключения к набору матричных строк.

    Схема подходит не для всех комбинаций опций — привязка описывает, для какого
    набора выбранных строк схема валидна («есть или нет»).
    """
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_wiring_diagram_bindings',
        verbose_name=_("Серия"),
        help_text=_("Серия, для которой актуальна схема (null — любая)")
    )
    body = models.ForeignKey(
        'ElectricActuatorBody', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_wiring_diagram_bindings',
        verbose_name=_("Корпус"),
        help_text=_("Корпус, для которого актуальна схема: модели общего корпуса "
                    "(QUI-варианты) делят клеммник/схему (null — любой)")
    )
    model_line_item = models.ForeignKey(
        'ElectricActuatorModelLineItem', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_wiring_diagram_bindings',
        verbose_name=_("Модель"),
        help_text=_("Модель, для которой актуальна схема (null — любая)")
    )
    control_unit = models.ForeignKey(
        'params.ControlUnitInstalledOption', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_wiring_diagram_bindings',
        verbose_name=_("Блок управления")
    )
    power_supply = models.ForeignKey(
        'params.PowerSupplies', on_delete=models.CASCADE, null=True, blank=True,
        related_name='ea_wiring_diagram_bindings',
        verbose_name=_("Напряжение питания")
    )
    mode = models.CharField(
        max_length=20, choices=EaMatrixMode.choices, null=True, blank=True,
        verbose_name=_("Режим"),
        help_text=_("Режим, для которого актуальна схема (null — любой)")
    )
    signals = models.ManyToManyField(
        EaSignalMatrixEntry, blank=True,
        related_name='wiring_diagram_bindings',
        verbose_name=_("Подпись сигналов"),
        help_text=_("Набор матричных строк, для которых валидна схема")
    )
    match_type = models.CharField(
        max_length=10, choices=EaDiagramMatchType.choices,
        default=EaDiagramMatchType.EXACT,
        verbose_name=_("Тип совпадения"),
        help_text=_("exact — выбор совпадает с подписью; superset — подпись ⊆ выбор")
    )
    diagram = models.ForeignKey(
        'media_library.MediaLibraryItem', on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'category__code': 'SCHEMA'},
        related_name='ea_wiring_diagram_bindings',
        verbose_name=_("Схема подключения"),
        help_text=_("Изображение из медиабиблиотеки (категория «Схема»)")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Название"),
        help_text=_("Например «AR01 INT 380В станд.»")
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Привязка схемы подключения ЭП")
        verbose_name_plural = _("Привязки схем подключения ЭП")
        ordering = ['sorting_order', 'id']

    def __str__(self):
        return self.name or f'Схема #{self.pk}'
