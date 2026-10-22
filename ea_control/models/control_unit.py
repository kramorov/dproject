# ea_control/models/control_unit.py
"""
Сущность «Блок управления» (тип БУ) электропривода.

``ControlUnit`` — физическая модель (без суффикса роли, по соглашению об
именах slots.md): конкретный тип блока управления производителя. Тип БУ
характерен для серии (все модели серии делят его); у разных серий БУ могут
совпадать или различаться.

Место в схеме паттерна (slots.md → «Решение: граница»): БУ — **опция внутри
изделия**, а не узел дерева EquipmentType (в дерево ничего не добавляем).
Связи с конфигурацией — через паттерн-модели:

- выбор БУ в конфигураторе — слот ``control_unit`` (slot_kind=object), опции
  которого ссылаются на записи этой модели;
- доступность БУ для серии/напряжения — строки матрицы слота ``control_unit``
  (замена AllowedControlUnitOption);
- дефолты слотов БУ — профильные (бесскоуповые) строки CuMatrixEntry;
- динамика конфигуратора — CuSlotRule.

Поля — только физика, без композитных данных (slots.md «Физика vs паттерн»):

- ``brand`` — производитель (producers.Brands — глобальная модель, не копируем);
- ``code`` — код типа БУ, уникален в рамках бренда;
- ``name``/``description`` — ru-поля для админки; i18n — миксином;
- ``kind`` — класс БУ: без БУ / базовый / интеллектуальный / позиционер;
- ``location`` — место размещения (CuLocationOption — копия справочника);
- ``accepts``/``emits``/``protocols`` — жёсткая физика клемм: какие команды
  принимает, какие сигналы ОС выдаёт, какие шины поддерживает (M2M на копии
  справочников CuControlSignal/CuFeedbackSignal/CuCommProtocol);
- ``capabilities`` — набор дополнительных возможностей, не покрытых слотами
  (PST, datalogger, ESD…; справочник CuCapability, M2M);
- ``control_voltage`` — напряжение цепей управления (params.PowerSupplies —
  глобальный справочник; null = напряжение задаёт форма сигнала);
- ``signal_power`` — источник и напряжение цепей управления по умолчанию
  (CuSignalPower);
- ``legacy_cu`` — 1:1-маппинг на params.ControlUnitInstalledOption до
  миграции (перенос данных — командами фазы 3).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, LocalizedDictFieldsMixin, TemplateMixin
from core.utils.localization import localized_name


class ControlUnitKind(models.TextChoices):
    """Класс блока управления."""
    NONE = 'NONE', _('Без блока управления')
    BASIC = 'BASIC', _('Базовый')
    INTEGRATED = 'INTEGRATED', _('Интеллектуальный')
    POSITIONER = 'POSITIONER', _('Позиционер')


class ControlUnit(TemplateMixin, CopyMixin, LocalizedDictFieldsMixin):
    """Тип блока управления электропривода производителя.

    Шаблоны (идея «БУ сам себя описывает»): модель несёт собственные шаблоны
    названия/описания/спецификации + ``_i18n``-переводы. Фолбэк-цепочка
    стандарта (свой шаблон → EquipmentType → дефолт) подключается аддитивно:
    при появлении узла-категории «БУ ЭП» добавляется FK ``equipment_type`` —
    ``TemplateMixin._get_equipment_type()`` сам найдёт его и подхватит
    шаблоны узла как дефолт (slots.md → «Решение: граница»). Пока узла нет —
    работают только собственные шаблоны; пустой шаблон = генерация не
    выполняется (остаётся поле name/description).

    Внимание: ``TemplateMixin.save()`` автоматически обновляет ``name``/
    ``description`` из шаблонов при каждом сохранении (если шаблон не пуст);
    сохранить без перегенерации — ``save(skip_auto_generate=True)``.
    """

    brand = models.ForeignKey(
        'producers.Brands', on_delete=models.PROTECT,
        related_name='control_units',
        verbose_name=_("Бренд"),
        help_text=_("Производитель БУ"),
    )
    code = models.CharField(
        max_length=50,
        verbose_name=_("Код"),
        help_text=_("Код типа БУ (уникален в рамках бренда), например «INT»"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название типа БУ, например «Интеллектуальный блок INT»"),
    )
    kind = models.CharField(
        max_length=20, choices=ControlUnitKind.choices,
        default=ControlUnitKind.BASIC,
        verbose_name=_("Класс БУ"),
        help_text=_("Без БУ / базовый / интеллектуальный / позиционер"),
    )
    location = models.ForeignKey(
        'CuLocationOption', on_delete=models.PROTECT, null=True, blank=True,
        related_name='control_units',
        verbose_name=_("Место размещения"),
        help_text=_("Где размещается БУ (встроен, навесной, шкаф…)"),
    )
    accepts = models.ManyToManyField(
        'CuControlSignal', blank=True,
        related_name='control_units',
        verbose_name=_("Принимает команды"),
        help_text=_("Какие командные сигналы БУ принимает (физика входов)"),
    )
    emits = models.ManyToManyField(
        'CuFeedbackSignal', blank=True,
        related_name='control_units',
        verbose_name=_("Выдаёт сигналы ОС"),
        help_text=_("Какие сигналы обратной связи БУ выдаёт (физика выходов)"),
    )
    protocols = models.ManyToManyField(
        'CuCommProtocol', blank=True,
        related_name='control_units',
        verbose_name=_("Протоколы"),
        help_text=_("Шинные протоколы, которые поддерживает БУ "
                    "(HART — атрибут сигнала, сюда не входит)"),
    )
    capabilities = models.ManyToManyField(
        'CuCapability', blank=True,
        related_name='control_units',
        verbose_name=_("Функции БУ"),
        help_text=_("Набор дополнительных возможностей, не покрытых слотами "
                    "(PST, datalogger, ESD, PID…)"),
    )
    control_voltage = models.ForeignKey(
        'params.PowerSupplies', on_delete=models.PROTECT, null=True, blank=True,
        related_name='cu_control_voltage_units',
        verbose_name=_("Напряжение цепей управления"),
        help_text=_("Номинал цепей управления БУ (24 В DC / 115 В AC…); "
                    "null — напряжение задаёт форма сигнала"),
    )
    signal_power = models.ForeignKey(
        'CuSignalPower', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='control_units',
        verbose_name=_("Питание цепей управления"),
        help_text=_("Источник × напряжение цепей управления по умолчанию"),
    )
    legacy_cu = models.OneToOneField(
        'params.ControlUnitInstalledOption', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='new_control_unit',
        verbose_name=_("Legacy-справочник"),
        help_text=_("1:1-маппинг на params.ControlUnitInstalledOption до "
                    "миграции данных"),
    )
    name_template = models.TextField(
        null=True, blank=True,
        verbose_name=_("Шаблон названия"),
        help_text=_("Плейсхолдеры из _get_data_dict: {code}, {brand}, {kind}, "
                    "{name}, {location}, {control_voltage}, {protocols}, "
                    "{capabilities}. Пусто — генерация не выполняется"),
    )
    description_template = models.TextField(
        null=True, blank=True,
        verbose_name=_("Шаблон описания"),
        help_text=_("Те же плейсхолдеры, что у шаблона названия"),
    )
    spec_template = models.JSONField(
        null=True, blank=True,
        verbose_name=_("Шаблон спецификации"),
        help_text=_("Структура секций: {\"Основные\": {\"Класс БУ\": "
                    "\"_res_kind\"}} — метка → путь поля или resolver"
                    "(_res_*)"),
    )
    name_template_i18n = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Переводы шаблона названия (ru/en/cn)"),
    )
    description_template_i18n = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Переводы шаблона описания (ru/en/cn)"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Текстовое описание типа БУ"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Блок управления")
        verbose_name_plural = _("Блоки управления")
        ordering = ['brand', 'sorting_order', 'code']
        unique_together = ['brand', 'code']
        indexes = [
            models.Index(fields=['kind']),
        ]

    def __str__(self):
        return f"{self.brand} — {self.name}" if self.name else self.code

    # ── Шаблоны (TemplateMixin): БУ сам себя описывает ─────────────────────
    # Поля name_template/description_template объявлены выше и затеняют
    # одноимённые property миксина; хуки ниже отдают их как источник,
    # чтобы переводы (_get_template_i18n) брались из тех же собственных
    # полей. Фолбэк на EquipmentType подключается позже (см. docstring
    # класса) — тогда переопределяем _resolve_template цепочкой
    # свой → EquipmentType → дефолт.

    def _get_name_template_source(self):
        """Собственный шаблон названия БУ (или None)."""
        return self.name_template or None

    def _get_description_template_source(self):
        """Собственный шаблон описания БУ (или None)."""
        return self.description_template or None

    def _get_template_i18n(self, field_base):
        """Переводы шаблона — из собственных *_i18n полей."""
        return getattr(self, f'{field_base}_i18n', None) or None

    def _get_data_dict(self, locale=None):
        """Плейсхолдер → путь/resolver для шаблонов БУ."""
        return {
            '{model_code}': 'code',
            '{code}': 'code',
            '{name}': 'name',
            '{brand}': 'brand',
            '{kind}': '_res_kind',
            '{location}': 'location',
            '{control_voltage}': 'control_voltage',
            '{protocols}': '_res_protocols',
            '{capabilities}': '_res_capabilities',
        }

    def _res_kind(self, locale=None):
        return self.get_kind_display()

    def _res_signal_power(self, locale=None):
        if not self.signal_power_id:
            return ''
        return localized_name(self.signal_power, locale)

    def _res_protocols(self, locale=None):
        names = [localized_name(p, locale) for p in self.protocols.all()]
        return ', '.join(names)

    def _res_capabilities(self, locale=None):
        names = [localized_name(c, locale) for c in self.capabilities.all()]
        return ', '.join(names)

    def generate_spec_sections(self):
        """Рендер секций спецификации БУ: {секция: {метка: значение}}.

        Структура из spec_template; значение метки — путь поля или
        resolver-метод (_res_*) — резолвится через
        TemplateMixin._resolve_data_dict_target.
        """
        result = {}
        for section, fields in (self.spec_template or {}).items():
            result[section] = {
                label: self._resolve_data_dict_target(path)
                for label, path in fields.items()
            }
        return result
