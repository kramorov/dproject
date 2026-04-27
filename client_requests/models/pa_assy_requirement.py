import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from client_requests.models import ClientRequestItem
from pneumatic_actuators.models import PneumaticActuatorModelLineItem, PneumaticActuatorBody, \
    PneumaticCloseTimeParameter, PneumaticActuatorVariety, PneumaticActuatorModelLine
from pneumatic_actuators.models.py_options_constants import SAFETY_POSITION_NC_DEFAULT_CODE , \
    ACTUATOR_VARIETY_RP_DEFAULT_CODE
from params.models import (MountingPlateTypes, StemShapes, StemSize, ThreadTypes, PneumaticConnection, ThreadSize,
                           ValveFunctionVariety, SealingClass, WarrantyTimePeriodVariety, ValveActuationVariety,
                           OptionVariety, ValveTypes, DnVariety, PnVariety, PneumaticAirSupplyPressure,
                           SafetyPositionOption, IpOption, ExdOption, BodyCoatingOption, HandWheelInstalledOption)

class PaAssyRequirement(models.Model):
    """
    Модель требований к сборке пневмопривода с ручным дублером, распределителем или позиционером,
     Фильтр-регулятором, фитингами (связана с позицией запроса)
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Связь с позицией запроса
    request_item = models.OneToOneField(
        ClientRequestItem,
        on_delete=models.CASCADE,
        related_name='pneumatic_requirement',
        verbose_name=_("Позиция запроса")
    )

    # === ПАРАМЕТРЫ АРМАТУРЫ ===
    valve_type = models.ForeignKey(
        ValveTypes,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Тип арматуры")
    )
    dn = models.ForeignKey(
        DnVariety,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("DN")
    )
    pn = models.ForeignKey(
        PnVariety,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("PN")
    )
    mounting_plate = models.ForeignKey(
        MountingPlateTypes,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Монтажная площадка")
    )
    stem_shape = models.ForeignKey(
        StemShapes,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Форма штока")
    )
    stem_size = models.ForeignKey(
        StemSize,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Шток")
    )

    # === МОМЕНТЫ ===
    torque_without_safety = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name=_("Момент без запаса (Нм)")
    )
    safety_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.3'),
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        verbose_name=_("Коэффициент запаса")
    )
    torque_with_safety = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name=_("Момент с запасом (Нм)")
    )

    # === ТРЕБОВАНИЯ К ПРИВОДУ ===
    air_pressure = models.ForeignKey(
        PneumaticAirSupplyPressure,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Давление в пневмосистеме")
    )
    actuator_variety = models.ForeignKey(
        PneumaticActuatorVariety,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Вид пневмопривода (DA/SR)")
    )
    safety_position = models.ForeignKey(
        SafetyPositionOption,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Положение безопасности (NO/NC)")
    )

    # === ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ ===
    ip_protection = models.ForeignKey(
        IpOption,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("IP защита")
    )
    exd_protection = models.ForeignKey(
        ExdOption,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Exd взрывозащита")
    )
    coating = models.ForeignKey(
        BodyCoatingOption,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Покрытие корпуса")
    )
    hand_wheel = models.ForeignKey(
        HandWheelInstalledOption,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Ручной дублер")
    )

    # === ТЕМПЕРАТУРНЫЕ УСЛОВИЯ ===
    temp_min = models.IntegerField(
        default=0,
        verbose_name=_("Минимальная температура (°C)")
    )
    temp_max = models.IntegerField(
        default=0,
        verbose_name=_("Максимальная температура (°C)")
    )
    # === УПРАВЛЕНИЕ И ОБРАТНАЯ СВЯЗЬ ===
    # Тип управления определяет логику: On/Off (распределитель) или Регулирующий (позиционер)
    control_type = models.CharField(
        max_length=20,
        choices=[('on_off', 'Отсечной (On/Off)'), ('modulating', 'Регулирующий')],
        default='on_off',
        verbose_name=_("Тип управления")
    )

    # Распределитель (Solenoid Valve)
    needs_solenoid = models.BooleanField(default=False, verbose_name=_("Требуется распределитель"))
    solenoid_voltage = models.CharField(max_length=50, blank=True,
                                        verbose_name=_("Напряжение катушки (24DC, 220AC...)"))

    # Позиционер (Positioner)
    needs_positioner = models.BooleanField(default=False, verbose_name=_("Требуется позиционер"))
    positioner_signal = models.CharField(max_length=50, default="4-20 mA", verbose_name=_("Входной сигнал"))
    positioner_protocol = models.CharField(max_length=50, blank=True, verbose_name=_("Протокол (HART, и т.д.)"))

    # Обратная связь (БКВ или встроенная в позиционер)
    needs_limit_switches = models.BooleanField(default=False, verbose_name=_("Требуется БКВ (Limit Switch Box)"))
    feedback_type = models.CharField(
        max_length=50,
        choices=[
            ('mechanical', 'Механические сухие контакты'),
            ('inductive', 'Индуктивные датчики'),
            ('analog_4_20', 'Аналоговый сигнал 4-20мА'),
            ('digital', 'Цифровой протокол (HART/Bus)'),
            ('positioner_integrated', 'Встроено в позиционер'),
        ],
        blank=True,
        verbose_name=_("Тип обратной связи")
    )

    # === ПОДГОТОВКА ВОЗДУХА (ФИЛЬТР-РЕГУЛЯТОР) ===
    needs_filter_regulator = models.BooleanField(default=False, verbose_name=_("Требуется фильтр-регулятор"))
    filter_drain_type = models.CharField(
        max_length=20,
        choices=[('manual', 'Ручной'), ('semi_auto', 'Полуавтомат'), ('auto', 'Автоматический')],
        default='manual',
        verbose_name=_("Тип спуска конденсата")
    )

    # === ОБВЯЗКА (ФИТИНГИ И ТРУБКА) ===
    needs_fittings = models.BooleanField(default=False, verbose_name=_("Требуются фитинги и трубка"))
    tube_material = models.CharField(max_length=50, blank=True, verbose_name=_("Материал трубки (Rilsan, Н/Ж...)"))
    tube_diameter = models.CharField(max_length=20, blank=True, verbose_name=_("Диаметр трубки (6, 8, 10 мм)"))
    fittings_material = models.CharField(max_length=50, blank=True, verbose_name=_("Материал фитингов"))

    # === МЕТАДАННЫЕ ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Требования к пневмоприводу")
        verbose_name_plural = _("Требования к пневмоприводу")

    def __str__(self):
        return f"Требования для {self.request_item}"