# valve_data/models/torque_characteristics.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import LocalizedDictFieldsMixin, OptionListToSelectMixin
from core.utils.localization import localized_name
from params.models import ValveTypes

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

    Единая точка истины для кодов точек со стороны привода (таблица моментов).
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


class ValveTorqueCoefficient(LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Таблица коэффициентов момента арматуры.

    Одна запись = одна таблица для конкретного типа арматуры × опоры ×
    уплотнения, внутри — шесть значений кривой BTO…ETC. К сериям арматуры
    привязывается через ``ValveLine.valve_torque_coefficient`` (одна таблица
    может висеть на нескольких сериях).
    """

    name = models.CharField(max_length=200, verbose_name=_('Название'))
    code = models.CharField(max_length=50, unique=True, verbose_name=_('Код'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))

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

    bto = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True,
                              verbose_name=_('BTO'),
                              help_text=_('Break to open — срыв с седла в начале открытия (0°)'))
    rto = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True,
                              verbose_name=_('RTO'),
                              help_text=_('Run to open — середина хода открытия'))
    eto = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True,
                              verbose_name=_('ETO'),
                              help_text=_('End to open — конец открытия (90°)'))
    btc = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True,
                              verbose_name=_('BTC'),
                              help_text=_('Break to close — начало закрытия (90°)'))
    rtc = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True,
                              verbose_name=_('RTC'),
                              help_text=_('Run to close — середина хода закрытия'))
    etc = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True,
                              verbose_name=_('ETC'),
                              help_text=_('End to close — посадка в седло в конце закрытия (0°)'))
    source = models.CharField(max_length=200, blank=True, verbose_name=_('Источник'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Порядок сортировки'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))

    class Meta:
        verbose_name = _('Коэффициент момента арматуры')
        verbose_name_plural = _('Коэффициенты момента арматуры')
        ordering = ['valve_type__sorting_order', 'sorting_order', 'id']

    def __str__(self):
        parts = [str(self.valve_type)]
        if self.support:
            parts.append(localized_name(self.support))
        if self.seal_type:
            parts.append(localized_name(self.seal_type))
        return ' — '.join(parts)

    @property
    def factors(self):
        """Кривая {code: float} — только заполненные точки, в порядке BTO…ETC."""
        return {code: float(getattr(self, code))
                for code in TORQUE_POINTS if getattr(self, code) is not None}

    def mirror_close_from_open(self):
        """Заполнить закрытие зеркалом открытия (по позиции хода).

        btc←eto, rtc←rto, etc←bto. Заполняются только пустые точки закрытия.
        Возвращает True, если что-то изменилось.
        """
        changed = False
        for open_code, close_code in (('eto', 'btc'), ('rto', 'rtc'), ('bto', 'etc')):
            if getattr(self, close_code) is None and getattr(self, open_code) is not None:
                setattr(self, close_code, getattr(self, open_code))
                changed = True
        return changed
