# valve_data/models/torque_characteristics.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import TemplateMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin
from core.utils.localization import localized_name
from params.models import ValveTypes
from pa_controls.models import ActingType

# Порядок шести точек (как в справочнике коэффициентов AUTORUN).
# Для линейных (4 точки) используются первые четыре: BTO, RTO, ETO, BTC.
TORQUE_POINTS = ('bto', 'rto', 'eto', 'btc', 'rtc', 'etc')


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


class TorqueThrustCharacteristics(models.Model):
    """Справочник характеристик момента/усилия арматуры.

    Набор коэффициентов для расчёта требуемого момента (ротационные — 6 точек)
    или усилия (линейные — 4 точки) по базовому значению:

        требуемое[i] = базовое[i] × коэффициент[i]

    Сейчас выбирается вручную в конфигураторе подбора пневмопривода; в будущем
    привязывается к серии арматуры для автоматического подбора привода.
    """

    code = models.CharField(max_length=50, unique=True, verbose_name=_('Код'))
    name = models.CharField(max_length=200, verbose_name=_('Название'))
    motion_type = models.ForeignKey(
        ActingType, on_delete=models.PROTECT, null=True, blank=True,
        related_name='torque_characteristics',
        verbose_name=_('Тип движения'),
        help_text=_('Ротационный (6 точек) или линейный (4 точки); коды LINEAR/ROTARY'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Порядок сортировки'))

    class Meta:
        verbose_name = _('Характеристики момента/усилия')
        verbose_name_plural = _('Характеристики момента/усилия')
        ordering = ['sorting_order', 'id']

    def __str__(self):
        return self.name


class ValveTorqueCoefficient(TemplateMixin, models.Model):
    """Коэффициенты момента для типа арматуры (6 точек BTO…ETC).

    Составной ключ — тип арматуры + опора пробки + уплотнение
    (``valve_type`` + ``support`` + ``seal_type``). Название генерируется по
    стандарту TemplateMixin.
    Точки (порядок ``TORQUE_POINTS``):
      BTO — Break To Open (страгивание на открытие);
      RTO — Running To Open (промежуточный момент открытия);
      ETO — End To Open (конечный момент открытия);
      BTC — Beginning To Close (страгивание на закрытие);
      RTC — Running To Close (промежуточный момент закрытия);
      ETC — End To Close (момент посадки в уплотнение при закрытии).
    """

    characteristics = models.ForeignKey(
        TorqueThrustCharacteristics, on_delete=models.CASCADE,
        related_name='valve_coefficients',
        verbose_name=_('Характеристики'),
        help_text=_('Набор характеристик, к которому относится коэффициент'))

    valve_type = models.ForeignKey(
        ValveTypes, on_delete=models.CASCADE, related_name='torque_coefficients',
        verbose_name=_('Тип арматуры'),
        help_text=_('Тип арматуры, к которому применяются коэффициенты'))

    support = models.ForeignKey(
        ValveSupportType, on_delete=models.PROTECT, null=True, blank=True,
        related_name='torque_coefficients',
        verbose_name=_('Тип опоры пробки'),
        help_text=_('Плавающая пробка / на цапфах (только для шаровых кранов)'))

    seal_type = models.ForeignKey(
        SealType, on_delete=models.PROTECT, null=True, blank=True,
        related_name='torque_coefficients',
        verbose_name=_('Тип уплотнения'),
        help_text=_('Мягкое / жёсткое (металл-металл) / PTFE'))

    # Генерируемые TemplateMixin поля.
    name = models.CharField(max_length=200, blank=True, verbose_name=_('Название'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    code = models.CharField(max_length=100, blank=True, verbose_name=_('Код'))

    # Рабочие коэффициенты (умножаются на базовый момент).
    bto = models.DecimalField(max_digits=6, decimal_places=3, verbose_name=_('Коэффициент BTO'),
                              help_text=_('Break To Open — страгивание на открытие'))
    rto = models.DecimalField(max_digits=6, decimal_places=3, verbose_name=_('Коэффициент RTO'),
                              help_text=_('Running To Open — промежуточный момент открытия'))
    eto = models.DecimalField(max_digits=6, decimal_places=3, verbose_name=_('Коэффициент ETO'),
                              help_text=_('End To Open — конечный момент открытия'))
    btc = models.DecimalField(max_digits=6, decimal_places=3, verbose_name=_('Коэффициент BTC'),
                              help_text=_('Beginning To Close — страгивание на закрытие'))
    rtc = models.DecimalField(max_digits=6, decimal_places=3, verbose_name=_('Коэффициент RTC'),
                              help_text=_('Running To Close — промежуточный момент закрытия'))
    etc = models.DecimalField(max_digits=6, decimal_places=3, verbose_name=_('Коэффициент ETC'),
                              help_text=_('End To Close — момент посадки в уплотнение'))

    # Нижние границы коэффициентов (для ручной настройки в UI).
    minimum_factors = models.JSONField(
        default=list, blank=True, verbose_name=_('Минимальные коэффициенты'),
        help_text=_('JSON-массив из 6 значений в порядке BTO, RTO, ETO, BTC, RTC, ETC'))

    # Отображаемые значения/диапазоны (числа или строки вида '90%~80%').
    values_display = models.JSONField(
        default=list, blank=True, verbose_name=_('Отображаемые значения'),
        help_text=_('JSON-массив из 6 значений; диапазоны — строками вида «90%~80%»'))

    source = models.CharField(max_length=200, blank=True, verbose_name=_('Источник'),
                              help_text=_('Откуда взяты коэффициенты (например, AUTORUN 报价系统)'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Порядок сортировки'))

    # ── Реестр полей шаблонов (TemplateMixin) ──
    TEMPLATE_FIELDS = (
        {'key': 'code', 'placeholder': '{model_code}', 'path': 'code', 'code_path': 'code'},
        {'key': 'valve_type', 'placeholder': '{valve_type}',
         'path': 'valve_type__name', 'code_path': 'valve_type__code'},
        {'key': 'support', 'placeholder': '{support}',
         'resolver': '_support_display', 'code_path': 'support__code'},
        {'key': 'seal_type', 'placeholder': '{seal_type}',
         'resolver': '_seal_type_display', 'code_path': 'seal_type__code'},
    )
    NAME_FIELD_KEYS = ('valve_type', 'support', 'seal_type')
    CODE_FIELD_KEYS = ('valve_type', 'support', 'seal_type')

    class Meta:
        verbose_name = _('Коэффициент момента арматуры')
        verbose_name_plural = _('Коэффициенты момента арматуры')
        ordering = ['characteristics', 'sorting_order', 'id']
        unique_together = ('characteristics', 'valve_type', 'support', 'seal_type')

    def __str__(self):
        return self.name or super().__str__()

    def _get_name_template_source(self):
        return '{valve_type}{support}{seal_type}'

    def _get_description_template_source(self):
        return 'Коэффициенты момента: {valve_type}{support}{seal_type}'

    def _support_display(self, locale=None):
        """Отображаемое значение опоры пробки с ведущим разделителем (или пусто)."""
        if not self.support:
            return ''
        label = localized_name(self.support, locale)
        return f' — {label}' if label else ''

    def _seal_type_display(self, locale=None):
        """Отображаемое значение уплотнения с ведущим разделителем (или пусто)."""
        if not self.seal_type:
            return ''
        label = localized_name(self.seal_type, locale)
        return f' — {label}' if label else ''

    def save(self, *args, **kwargs):
        if not self.code and self.valve_type_id:
            parts = [self.valve_type.code]
            if self.support:
                parts.append(self.support.code)
            if self.seal_type:
                parts.append(self.seal_type.code)
            self.code = '-'.join(parts)
        super().save(*args, **kwargs)

    @property
    def factors(self) -> list:
        """Рабочие коэффициенты в порядке BTO, RTO, ETO, BTC, RTC, ETC."""
        return [float(getattr(self, p)) for p in TORQUE_POINTS]
