# pa_controls/models/posi_model_line.py
"""
Серия позиционеров (PosiModelLine) и through-опции уровня серии.

По образцу электроприводов (ea_options.py / ea_model_line.py):
каждая опция — through-модель, связывающая серию с вариантом из справочника
и хранящая encoding (код для артикула), is_default и sorting_order.
Из разрешённых опций серии собирается PosiModelLineItem.

Опции:
    PosiActingTypeOption          — тип действия (линейный/ротационный)
    PosiBodyConnectionOption      — присоединения корпуса (резьбы пневмовхода/выхода + отверстие КВ)
    PosiLeverOption               — рычаг (тип + диапазон хода штока)
    PosiTemperatureOption         — температурное исполнение (мин/макс)
    PosiSignalProfileOption       — профиль сигналов (обратная связь)
    PosiAlarmOption               — сигнал тревоги (профиль сигналов с ролью «Авария»)

Взрывозащита — не through-опция, а список значений (M2M) на самой серии.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import StructuredDataMixin, EquipmentTypeMixin, TechDocMixin, ImageGalleryMixin
from core.models.cert_doc_mixin import CertDocMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from producers.models import Producer, Brands
from materials.models import MaterialGeneral

from options.models import (
    BaseThroughOption,
    BaseTemperatureThroughOption,
)

from .posi_options import ActingType, LeverOption, SmartCapabilitySet


class PosiModelLine(ImageGalleryMixin, TechDocMixin, CertDocMixin, EquipmentTypeMixin,
                    SmartCatalogMixin, StructuredDataMixin, models.Model):
    """Серия позиционеров (аналог LimitSwitchModelLine для БКВ).

    Характеристики уровня серии (общие для всех моделей серии):
      - body_material — материал корпуса (есть серии, отличающиеся только материалом);
      - weight — вес, кг (зависит от материала);
      - actuator_action — для каких пневмоприводов: DA / SR / оба (TextChoices ActuatorAction);
      - supply_pressure_min/max — диапазон давления питания, бар;
      - exd — список доступных степеней взрывозащиты (M2M, не through-опция);
      - smart_capability_set — набор смарт-возможностей (FK);
      - extra_params — air_consumption, linearity, hysteresis и пр. в JSON.

    Опции серии — through-модели в этом же модуле (по образцу электроприводов):
    каждая связывает серию с вариантом справочника и хранит encoding (код для
    артикула), is_default и sorting_order. Из разрешённых опций серии
    собирается PosiModelLineItem.

    Название и описание моделей формируются из name_template/description_template
    (см. PosiModelLineItem, TemplateMixin).
    """

    class ActuatorAction(models.TextChoices):
        DA = 'da', _('DA (двойного действия)')
        SR = 'sr', _('SR (пружинного возврата)')
        BOTH = 'both', _('DA/SR (для обоих)')

    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название серии позиционеров'))
    code = models.CharField(max_length=50, blank=True, null=True,
                            verbose_name=_("Код"),
                            help_text=_("Код серии"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание серии позиционеров'))
    name_template = models.TextField(blank=True, null=True,
                                     verbose_name=_("Шаблон названия"),
                                     help_text=_('Шаблон для текстового названия позиционера'))
    description_template = models.TextField(blank=True, null=True,
                                            verbose_name=_("Шаблон описания"),
                                            help_text=_('Шаблон для описания позиционера'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    producer = models.ForeignKey(Producer, related_name='posi_model_line_producer', blank=True,
                                 null=True, on_delete=models.SET_NULL,
                                 help_text=_('Производитель позиционеров'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, related_name='posi_model_line_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд позиционеров'),
                              verbose_name=_("Бренд"))
    # Взрывозащита — список значений серии (не through-опция)
    exd = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='+',
        help_text=_('Список доступных степеней взрывозащиты серии'),
        verbose_name=_("Взрывозащита")
    )

    # ── Характеристики серии ──
    body_material = models.ForeignKey(
        MaterialGeneral, related_name='posi_model_line_body_material',
        blank=True, null=True, on_delete=models.SET_NULL,
        help_text=_('Материал корпуса (есть серии, отличающиеся только материалом)'),
        verbose_name=_("Материал корпуса")
    )
    weight = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("Вес, кг"),
        help_text=_('Вес позиционера (зависит от материала корпуса)')
    )
    actuator_action = models.CharField(
        max_length=10,
        choices=ActuatorAction.choices,
        default=ActuatorAction.BOTH,
        verbose_name=_("Тип пневмопривода"),
        help_text=_('Для каких пневмоприводов: DA, SR или для обоих')
    )
    supply_pressure_min = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("Мин. давление питания (бар)")
    )
    supply_pressure_max = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("Макс. давление питания (бар)")
    )
    # Смарт-возможности — единый справочник, набор привязывается к серии
    smart_capability_set = models.ForeignKey(
        SmartCapabilitySet,
        related_name='posi_model_lines',
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Набор смарт-возможностей")
    )

    extra_params = models.JSONField(default=dict, blank=True,
                                    verbose_name=_("Параметры"),
                                    help_text=_("Дополнительные параметры серии: "
                                                "air_consumption, linearity, hysteresis и т.д."))

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Серия позиционеров')
        verbose_name_plural = _('Серии позиционеров')

    def __str__(self):
        return self.name


# ============================================================
# THROUGH-ОПЦИИ УРОВНЯ СЕРИИ (как в электроприводах)
# ============================================================

class PosiActingTypeOption(BaseThroughOption):
    """Тип действия (линейный/ротационный), разрешённый для серии.

    Through-модель уровня серии: model_line + acting_type + encoding/is_default.
    """
    model_line = models.ForeignKey(
        PosiModelLine, on_delete=models.CASCADE,
        related_name='acting_type_options',
        verbose_name=_("Серия позиционеров")
    )
    acting_type = models.ForeignKey(
        ActingType, on_delete=models.CASCADE,
        verbose_name=_("Тип действия")
    )

    class Meta:
        verbose_name = _("Тип действия для серии позиционеров")
        verbose_name_plural = _("Типы действия для серий позиционеров")
        ordering = ['is_default', 'sorting_order']
        unique_together = ['model_line', 'acting_type']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    def __str__(self):
        return f"{self.model_line} → {self.acting_type} ({self.encoding})"


class PosiBodyConnectionOption(BaseThroughOption):
    """Присоединения корпуса, разрешённые для серии.

    Связывает серию со справочником PosiBodyConnections (резьбы
    пневмовхода/выхода + отверстие под кабельный ввод). Заменяет
    PosiPneumaticThreadOption, PosiPneumaticConnectionOption и
    PosiCableGlandHolesOption.

    only_non_ex — вариант доступен только в общепромышленном исполнении
    (запрещён при выборе взрывозащиты).
    """
    model_line = models.ForeignKey(
        PosiModelLine, on_delete=models.CASCADE,
        related_name='body_connection_options',
        verbose_name=_("Серия позиционеров")
    )
    body_connection = models.ForeignKey(
        'pa_controls.PosiBodyConnections', on_delete=models.CASCADE,
        related_name='model_line_options',
        verbose_name=_("Присоединения корпуса")
    )
    only_non_ex = models.BooleanField(
        default=False,
        verbose_name=_("Только общепром"),
        help_text=_('Вариант недоступен при выборе взрывозащиты')
    )

    class Meta:
        verbose_name = _("Присоединения корпуса для серии позиционеров")
        verbose_name_plural = _("Присоединения корпусов для серий позиционеров")
        ordering = ['is_default', 'sorting_order']
        unique_together = ['model_line', 'body_connection']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    def __str__(self):
        return f"{self.model_line} → {self.body_connection} ({self.encoding})"


class PosiLeverOption(BaseThroughOption):
    """Рычаг (длина и тип), разрешённый для серии.

    Through-модель уровня серии: model_line + lever (LeverOption) + encoding/is_default.
    """
    model_line = models.ForeignKey(
        PosiModelLine, on_delete=models.CASCADE,
        related_name='lever_options',
        verbose_name=_("Серия позиционеров")
    )
    lever = models.ForeignKey(
        LeverOption, on_delete=models.CASCADE,
        verbose_name=_("Рычаг")
    )

    class Meta:
        verbose_name = _("Рычаг для серии позиционеров")
        verbose_name_plural = _("Рычаги для серий позиционеров")
        ordering = ['is_default', 'sorting_order']
        unique_together = ['model_line', 'lever']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    def __str__(self):
        return f"{self.model_line} → {self.lever} ({self.encoding})"


class PosiTemperatureOption(BaseTemperatureThroughOption):
    """Температурное исполнение, разрешённое для серии.

    Диапазон хранится прямо в опции (work_temp_min/work_temp_max) — как в ЭП.
    У item температура выносится полями work_temp_min/max.

    only_non_ex — исполнение доступно только в общепромышленном варианте
    (например, High temperature -20…120°C запрещено для Ex).
    """
    model_line = models.ForeignKey(
        PosiModelLine, on_delete=models.CASCADE,
        related_name='temperature_options',
        verbose_name=_("Серия позиционеров")
    )
    only_non_ex = models.BooleanField(
        default=False,
        verbose_name=_("Только общепром"),
        help_text=_('Вариант недоступен при выборе взрывозащиты')
    )

    class Meta:
        verbose_name = _("Температурная опция серии позиционеров")
        verbose_name_plural = _("Температурные опции серий позиционеров")
        ordering = ['is_default', 'sorting_order']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    def __str__(self):
        return f"{self.model_line} → {self.work_temp_min}..{self.work_temp_max} °С ({self.encoding})"


class PosiSignalProfileOption(BaseThroughOption):
    """Профиль сигналов, разрешённый для серии.

    FK на params.ControlUnitSignalProfile: вход 4-20/HART + обратная связь.
    Для всех моделей по умолчанию подставляется POS-STD-4-20 (вход 4-20 мА) —
    см. PosiModelLineItem.save().

    only_non_ex — вариант обратной связи доступен только в общепромышленном
    исполнении (например, Position transmitter и HART запрещены для Ex).
    """
    model_line = models.ForeignKey(
        PosiModelLine, on_delete=models.CASCADE,
        related_name='signal_profile_options',
        verbose_name=_("Серия позиционеров")
    )
    signal_profile = models.ForeignKey(
        'params.ControlUnitSignalProfile', on_delete=models.CASCADE,
        verbose_name=_("Профиль сигналов")
    )
    only_non_ex = models.BooleanField(
        default=False,
        verbose_name=_("Только общепром"),
        help_text=_('Вариант недоступен при выборе взрывозащиты')
    )

    class Meta:
        verbose_name = _("Профиль сигналов для серии позиционеров")
        verbose_name_plural = _("Профили сигналов для серий позиционеров")
        ordering = ['is_default', 'sorting_order']
        unique_together = ['model_line', 'signal_profile']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    def __str__(self):
        return f"{self.model_line} → {self.signal_profile} ({self.encoding})"


class PosiAlarmOption(BaseThroughOption):
    """Сигнал тревоги, разрешённый для серии.

    Тревога описывается профилем сигналов с ролью «Вых. Авария» — FK на
    params.ControlUnitSignalProfile (отдельного справочника тревог нет).
    """
    model_line = models.ForeignKey(
        PosiModelLine, on_delete=models.CASCADE,
        related_name='alarm_options',
        verbose_name=_("Серия позиционеров")
    )
    alarm = models.ForeignKey(
        'params.ControlUnitSignalProfile', on_delete=models.CASCADE,
        verbose_name=_("Сигнал тревоги (профиль сигналов)")
    )

    class Meta:
        verbose_name = _("Сигнал тревоги для серии позиционеров")
        verbose_name_plural = _("Сигналы тревоги для серий позиционеров")
        ordering = ['is_default', 'sorting_order']
        unique_together = ['model_line', 'alarm']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    def __str__(self):
        return f"{self.model_line} → {self.alarm} ({self.encoding})"


class PosiExdOption(BaseThroughOption):
    """Взрывозащита, разрешённая для серии позиционеров.

    Одна строка = одна КОДИРОВКА (опция выбора), внутри — M2M видов взрывозащиты:
      * «Общепромышленное» — строка со своим encoding (например 'R'),
        M2M пустой (или ссылка на запись «Общепром» справочника);
      * «Ex» — строка с encoding 'Ex', в M2M — все доступные виды Exd
        (разная взрывозащита может делить один encoding).

    Кодировка уникальна в пределах серии (валидация BaseThroughOption),
    а виды Exd внутри кодировки перечислены M2M — поиск/фильтры по
    конкретному виду работают через exd_options__exd_options.
    """
    model_line = models.ForeignKey(
        PosiModelLine, on_delete=models.CASCADE,
        related_name='exd_options',
        verbose_name=_("Серия позиционеров")
    )
    exd_options = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='posi_model_line_exd_option_rows',
        verbose_name=_("Виды взрывозащиты")
    )

    class Meta:
        verbose_name = _("Взрывозащита для серии позиционеров")
        verbose_name_plural = _("Взрывозащита для серий позиционеров")
        ordering = ['is_default', 'sorting_order']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    def validate_unique_encoding(self) -> None:
        """Одна строка на кодировку в пределах серии.

        Базовая реализация пропускает НЕсохранённые объекты (adding) — для
        M2M-схемы это дыра, поэтому проверяем и при создании, и при правке:
        непустой encoding не должен повторяться в другой строке серии.
        """
        from django.core.exceptions import ValidationError as _ValidationError

        if not (self.encoding and self.encoding.strip()):
            return
        parent = getattr(self, self._get_parent_field_name(), None)
        if parent is None or getattr(parent, 'pk', None) is None:
            return
        existing = self.__class__.objects.filter(
            **{self._get_parent_field_name(): parent, 'encoding': self.encoding}
        ).exclude(pk=self.pk)
        if existing.exists():
            raise _ValidationError({
                'encoding': _('Кодировка "%(encoding)s" уже используется '
                              'в этой серии — добавьте вид в существующую строку.') % {
                    'encoding': self.encoding}
            })

    def __str__(self):
        values = ', '.join(e.name for e in self.exd_options.all()) or '—'
        return f"{self.model_line} → {self.encoding}: {values}"
