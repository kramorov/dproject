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


# Канонический набор значений справочников (единый источник для сидов ЭП и БУ).
FEEDBACK_DEVICE_KINDS = (
    ('POSITION_SENSOR', 'Датчик положения'),
    ('THERMAL_SENSOR', 'Датчик температуры (теплозащита)'),
)

FEEDBACK_TECHNOLOGIES = (
    ('POTENTIOMETER', 'Потенциометрический'),
    ('POT_CONVERTER', 'Потенциометр + преобразователь'),
    ('HALL', 'Датчик Холла'),
    ('MAGNETIC', 'Магнитный'),
    ('BIMETAL', 'Биметаллическое термореле'),
    ('PTC', 'PTC-термистор с реле оценки'),
    ('OTHER', 'Прочее'),
    ('MWG', 'Магнитно-волновой (MWG)'),
    ('ELECTRONIC', 'Электронный'),
    ('MECHANICAL', 'Механический'),
    ('ABSOLUTE_ENCODER', 'Абсолютный энкодер'),
    ('INDUCTIVE', 'Индуктивный'),
)


def _default_device_kind():
    """Дефолтная категория устройства (как было до перевода kind на FK)."""
    return EaFeedbackDeviceKind.objects.get_or_create(
        code='POSITION_SENSOR',
        defaults={'name': 'Датчик положения'})[0]


class EaFeedbackDeviceKind(CopyMixin, LocalizedDictFieldsMixin,
                           OptionListToSelectMixin):
    """Категория устройства ОС: позиционный датчик или теплозащита.

    Раньше была ``models.TextChoices`` — заменена на справочную модель, чтобы
    значения редактировались данными, а не хардкодом. Разделяется с БУ
    (``ea_control.CuFeedbackDevice`` ссылается на эту же модель).
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Категория устройства ОС")
        verbose_name_plural = _("Категории устройств ОС")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class EaFeedbackTechnology(CopyMixin, LocalizedDictFieldsMixin,
                           OptionListToSelectMixin):
    """Технология устройства ОС.

    Раньше была ``models.TextChoices`` — заменена на справочную модель.
    Значения объединены из ЭП и БУ (POT_CONVERTER/BIMETAL/PTC/OTHER из ЭП;
    MWG/ELECTRONIC/MECHANICAL/ABSOLUTE_ENCODER/INDUCTIVE из БУ).
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Технология устройства ОС")
        verbose_name_plural = _("Технологии устройств ОС")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


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
    kind = models.ForeignKey(
        EaFeedbackDeviceKind, on_delete=models.PROTECT,
        default=_default_device_kind,
        related_name='devices_by_kind',
        verbose_name=_("Категория"),
        help_text=_("Датчик положения (RWG/EWG/потенциометр) или теплозащита "
                    "(термореле/PTC)")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название устройства, например «RWG 4020»")
    )
    technology = models.ForeignKey(
        EaFeedbackTechnology, on_delete=models.PROTECT,
        related_name='devices_by_technology',
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
        verbose_name = _("Устройство ОС ЭП EaFeedbackDevice")
        verbose_name_plural = _("Устройства ОС ЭП")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name
