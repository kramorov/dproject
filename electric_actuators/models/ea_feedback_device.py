# electric_actuators/models/ea_feedback_device.py
"""
Справочник устройств позиционной обратной связи электроприводов.

``EaFeedbackDevice`` — собственный каталог ЭП (НЕ ``pa_controls.SensorComponent``:
у того другая семантика — закупаемые компоненты БКВ/позиционеров с variety/Ex/
моделями). Здесь — опции производителя привода с выходным сигналом:

    RWG_4020        — потенциометр + преобразователь → 0/4–20 мА (AUMA);
    EWG_01_1        — бесконтактный (Холл) позиционный трансмиттер 0/4–20 мА (AUMA);
    MWG             — магнитный датчик пределов/момента + аналог положения (AUMA);
    PRECISION_POT   — голый потенциометр (сопротивление наружу);
    TRANSMITTER_4_20 / POT_RAW — свои исполнения (AOX).

Зачем нужен при сигнальной модели: RWG и EWG дают одинаковый сигнал 4–20 мА, но
разную технологию — тендеры формулируют замену явно («аналог AUMA RWG/EWG»), а
значит форма сигнала и устройство различаются отдельно.

``emits`` — какие сигналы выдаёт устройство (MWG: контакты пределов/момента +
аналог положения). ``equivalents`` — эквивалентность «наш = их» (M2M self);
отсутствие связи честно показывает «аналога нет».

Локализация: ru-базовые поля + ``_i18n``-переводы; коды не переводятся.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import (CopyMixin, LocalizedDictFieldsMixin,
                                 OptionListToSelectMixin)


class EaFeedbackTechnology(models.TextChoices):
    """Технология устройства ОС."""
    POTENTIOMETER = 'POTENTIOMETER', _('Потенциометр')
    POT_CONVERTER = 'POT_CONVERTER', _('Потенциометр + преобразователь')
    HALL = 'HALL', _('Бесконтактный (датчики Холла)')
    MAGNETIC = 'MAGNETIC', _('Магнитный (пределы/момент/положение)')
    BIMETAL = 'BIMETAL', _('Биметаллическое термореле')
    PTC = 'PTC', _('PTC-термистор с реле оценки')
    OTHER = 'OTHER', _('Прочее')


class EaFeedbackDeviceKind(models.TextChoices):
    """Категория устройства ОС: позиционный датчик или теплозащита."""
    POSITION_SENSOR = 'POSITION_SENSOR', _('Датчик положения')
    THERMAL_SENSOR = 'THERMAL_SENSOR', _('Датчик температуры (теплозащита)')


class EaFeedbackDevice(CopyMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Устройство позиционной ОС электропривода.

    Справочный слой поверх сигнальной модели: описывает технологию и
    эквивалентность устройств конкурентов; доступность на моделях задаётся
    матрицей (``EaSignalMatrixEntry.device``).
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код устройства, например «RWG_4020», «MWG»")
    )
    kind = models.CharField(
        max_length=20, choices=EaFeedbackDeviceKind.choices,
        default=EaFeedbackDeviceKind.POSITION_SENSOR,
        verbose_name=_("Категория"),
        help_text=_("Датчик положения (RWG/EWG/потенциометр) или теплозащита "
                    "(термореле/PTC)")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название устройства, например «RWG 4020»")
    )
    technology = models.CharField(
        max_length=20, choices=EaFeedbackTechnology.choices,
        verbose_name=_("Технология"),
        help_text=_("Технология датчика: потенциометр, Холл, магнитный, …")
    )
    contactless = models.BooleanField(
        default=False,
        verbose_name=_("Бесконтактный"),
        help_text=_("Бесконтактное измерение (без износа)")
    )
    emits = models.ManyToManyField(
        'EaFeedbackSignal', blank=True,
        related_name='emitting_devices',
        verbose_name=_("Выдаёт сигналы"),
        help_text=_("Сигналы, которые устройство выдаёт (MWG: контакты + аналог)")
    )
    equivalents = models.ManyToManyField(
        'self', blank=True,
        verbose_name=_("Эквиваленты"),
        help_text=_("«Наш X ≡ их Y» (RWG_4020 и т.п.); отсутствие связи = аналога нет")
    )
    accuracy = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Точность"),
        help_text=_("Справочно: точность передачи положения")
    )
    life_cycles = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Ресурс"),
        help_text=_("Справочно: ресурс (циклы) или срок службы")
    )
    temp_range = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Температурный диапазон"),
        help_text=_("Справочно: допустимая температура, например «−60…+80 °C»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение устройства и примечания")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Устройство ОС ЭП")
        verbose_name_plural = _("Устройства ОС ЭП")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name
