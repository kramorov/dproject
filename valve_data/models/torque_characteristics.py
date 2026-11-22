# valve_data/models/torque_characteristics.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import LocalizedDictFieldsMixin, OptionListToSelectMixin
from core.utils.localization import localized_name
from params.models import ValveTypes
from pa_controls.models import ActingType

# Порядок шести точек (как в справочнике коэффициентов AUTORUN).
# Для линейных (4 точки) используются первые четыре: BTO, RTO, ETO, BTC.
TORQUE_POINTS = ('bto', 'rto', 'eto', 'btc', 'rtc', 'etc')

# Направления хода точки момента.
POINT_DIRECTION_OPEN = 'open'
POINT_DIRECTION_CLOSE = 'close'

# Позиции вдоль хода (для спаривания open/close при сравнении).
POINT_POSITION_START = 'start'
POINT_POSITION_MID = 'mid'
POINT_POSITION_END = 'end'

# Точки ротационного набора (6) и линейного (4).
POINT_SEED = [
    # code, направление, позиция, порядок
    ('bto', POINT_DIRECTION_OPEN, POINT_POSITION_START, 10),
    ('rto', POINT_DIRECTION_OPEN, POINT_POSITION_MID, 20),
    ('eto', POINT_DIRECTION_OPEN, POINT_POSITION_END, 30),
    ('btc', POINT_DIRECTION_CLOSE, POINT_POSITION_END, 40),   # начало закрытия = 90° (конец хода открытия)
    ('rtc', POINT_DIRECTION_CLOSE, POINT_POSITION_MID, 50),
    ('etc', POINT_DIRECTION_CLOSE, POINT_POSITION_START, 60),  # посадка в седло = 0°
]


class SealType(LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Тип уплотнения (материал седла): мягкое, жёсткое (металл-металл), PTFE.

    Справочник. Используется для классификации арматуры и коэффициентов момента.
    Стартовые записи: soft / hard / ptfe.
    """

    name = models.CharField(max_length=100, verbose_name=_('Название'))
    code = models.CharField(max_length=50, unique=True, verbose_name=_('Код'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Порядок сортировки'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))

    class Meta:
        verbose_name = _('Тип уплотнения')
        verbose_name_plural = _('Типы уплотнения')
        ordering = ['sorting_order', 'id']

    def __str__(self):
        return self.name


class ValveSupportType(LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Тип опоры пробки шарового крана: плавающая пробка или на цапфах.

    Справочник. Применяется только к шаровым кранам; для дисковых затворов и
    пробковых кранов не задаётся. Стартовые записи: floating / trunnion.
    """

    name = models.CharField(max_length=100, verbose_name=_('Название'))
    code = models.CharField(max_length=50, unique=True, verbose_name=_('Код'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Порядок сортировки'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))

    class Meta:
        verbose_name = _('Тип опоры пробки')
        verbose_name_plural = _('Типы опоры пробки')
        ordering = ['sorting_order', 'id']

    def __str__(self):
        return self.name


class TorquePoint(LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Справочник точек момента/усилия (BTO…ETC).

    Единая точка истины для кодов точек как со стороны арматуры
    (коэффициенты), так и со стороны привода (таблица моментов).

    ``direction`` — направление хода (open/close); ``position`` — позиция
    вдоль хода (start/mid/end). Спаривание открытие↔закрытие при сравнении
    выполняется по позиции (start↔start и т.д.), что даёт BTO↔ETC, RTO↔RTC,
    ETO↔BTC.
    """

    DIRECTION_CHOICES = [
        (POINT_DIRECTION_OPEN, _('Открытие')),
        (POINT_DIRECTION_CLOSE, _('Закрытие')),
    ]
    POSITION_CHOICES = [
        (POINT_POSITION_START, _('Начало хода')),
        (POINT_POSITION_MID, _('Середина хода')),
        (POINT_POSITION_END, _('Конец хода')),
    ]

    code = models.CharField(max_length=10, unique=True, verbose_name=_('Код'))
    name = models.CharField(max_length=20, verbose_name=_('Название'),
                            help_text=_('Краткое имя точки, например BTO'))
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name=_('Направление'))
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, verbose_name=_('Позиция хода'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Порядок сортировки'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))

    class Meta:
        verbose_name = _('Точка момента/усилия')
        verbose_name_plural = _('Точки момента/усилия')
        ordering = ['sorting_order', 'id']

    def __str__(self):
        return self.name or self.code

    def counterpart(self):
        """Точка противоположного направления на той же позиции хода."""
        return TorquePoint.objects.filter(
            position=self.position, is_active=True,
        ).exclude(id=self.id).exclude(direction=self.direction).first()

    @classmethod
    def seed(cls):
        """Создать стандартные 6 точек (ротационные; линейные используют 4 из них)."""
        for code, direction, position, order in POINT_SEED:
            cls.objects.update_or_create(
                code=code,
                defaults=dict(name=code.upper(), direction=direction, position=position,
                              sorting_order=order, is_active=True))


class TorqueThrustCharacteristics(models.Model):
    """Справочник характеристик момента/усилия арматуры.

    Набор коэффициентов для расчёта требуемого момента (ротационные — 6 точек)
    или усилия (линейные — 4 точки) по базовому значению:

        требуемое[i] = базовое[i] × коэффициент[i]

    Точки набора — M2M на TorquePoint (ротационный — 6, линейный — 4).
    """

    code = models.CharField(max_length=50, unique=True, verbose_name=_('Код'))
    name = models.CharField(max_length=200, verbose_name=_('Название'))
    motion_type = models.ForeignKey(
        ActingType, on_delete=models.PROTECT, null=True, blank=True,
        related_name='torque_characteristics',
        verbose_name=_('Тип движения'),
        help_text=_('Ротационный (6 точек) или линейный (4 точки); коды LINEAR/ROTARY'))
    points = models.ManyToManyField(
        TorquePoint, blank=True, related_name='characteristics_sets',
        verbose_name=_('Точки набора'),
        help_text=_('Какие точки входят в набор (ротационный — 6, линейный — 4)'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Порядок сортировки'))

    class Meta:
        verbose_name = _('Характеристики момента/усилия')
        verbose_name_plural = _('Характеристики момента/усилия')
        ordering = ['sorting_order', 'id']

    def __str__(self):
        return self.name

    @property
    def points_ordered(self):
        return list(self.points.order_by('sorting_order'))

    @property
    def point_codes(self):
        return [p.code for p in self.points_ordered]


class ValveTorqueCoefficient(models.Model):
    """Коэффициент момента арматуры в одной точке (длинный формат).

    Строка = (набор характеристик × тип арматуры × опора × уплотнение × точка).
    ``factor`` — рабочий коэффициент; ``min_factor`` — нижняя граница
    (для ручной настройки в UI); ``display`` — отображаемое значение
    (число или диапазон вида «90%~80%»).
    """

    characteristics = models.ForeignKey(
        TorqueThrustCharacteristics, on_delete=models.CASCADE,
        related_name='valve_coefficients',
        verbose_name=_('Характеристики'))

    valve_type = models.ForeignKey(
        ValveTypes, on_delete=models.CASCADE, related_name='torque_coefficients',
        verbose_name=_('Тип арматуры'))

    support = models.ForeignKey(
        ValveSupportType, on_delete=models.PROTECT, null=True, blank=True,
        related_name='torque_coefficients',
        verbose_name=_('Тип опоры пробки'))

    seal_type = models.ForeignKey(
        SealType, on_delete=models.PROTECT, null=True, blank=True,
        related_name='torque_coefficients',
        verbose_name=_('Тип уплотнения'))

    point = models.ForeignKey(
        TorquePoint, on_delete=models.PROTECT, related_name='valve_coefficients',
        verbose_name=_('Точка'))

    factor = models.DecimalField(max_digits=6, decimal_places=3, verbose_name=_('Коэффициент'),
                                 help_text=_('Рабочий коэффициент (умножается на базовый момент)'))
    min_factor = models.DecimalField(max_digits=6, decimal_places=3, default=0,
                                     blank=True, null=True,
                                     verbose_name=_('Минимальный коэффициент'))
    display = models.CharField(max_length=30, blank=True, verbose_name=_('Отображаемое значение'),
                               help_text=_('Число или диапазон вида «90%~80%»'))
    source = models.CharField(max_length=200, blank=True, verbose_name=_('Источник'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Порядок сортировки'))

    class Meta:
        verbose_name = _('Коэффициент момента арматуры')
        verbose_name_plural = _('Коэффициенты момента арматуры')
        ordering = ['characteristics', 'sorting_order', 'id']
        unique_together = ('characteristics', 'valve_type', 'support', 'seal_type', 'point')

    def __str__(self):
        parts = [str(self.valve_type)]
        if self.support:
            parts.append(localized_name(self.support))
        if self.seal_type:
            parts.append(localized_name(self.seal_type))
        parts.append(self.point.code.upper())
        return ' — '.join(parts)

    @classmethod
    def get_curve(cls, characteristics_id, valve_type_id, support_id=None, seal_type_id=None):
        """Кривая коэффициентов по точкам набора: {code: factor}.

        Порядок точек — из набора характеристик; точки, у которых нет строки,
        в кривую не попадают.
        """
        rows = cls.objects.filter(
            characteristics_id=characteristics_id,
            valve_type_id=valve_type_id,
            support_id=support_id,
            seal_type_id=seal_type_id,
            is_active=True,
        ).select_related('point')
        return {r.point.code: float(r.factor) for r in rows}
