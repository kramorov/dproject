# pneumatic_actuators/models/pa_item.py
"""
ЭТАЛОННАЯ каталожная модель пневмопривода — PneumaticActuatorCatalogItem.

Создана 2026-08-31 в рамках унификации каталогов. Работает по общему контракту
(как DirectionValve / LimitSwitchBox / FilterRegulator / GearBox / PneumaticFitting):

- Шаблоны name_template / description_template живут на model_line
  (PneumaticActuatorModelLine, поля добавляются отдельным шагом);
- Item переопределяет _get_name_template_source / _get_description_template_source
  → model_line, _get_default_* (fallback); словари плейсхолдеров выводятся из
  реестра TEMPLATE_FIELDS (pa_item_fields.py);
- Автогенерация name/description — в TemplateMixin.save()
  (пропускается флагом skip_auto_generate=True);
- save() = super().save() + sync_sku() — SKU создаётся из ЭТОЙ модели
  через SKUMixin (стандартный путь, как в остальных каталогах);
- Артикул (code) рендерится из model_line.model_item_code_template
  через _fill_template + CODE_FIELD_KEYS реестра (encoding опций из through-моделей).

Старые модели (PneumaticActuatorSelected, PneumaticActuatorConstructor,
PneumaticActuatorModelLineItem) НЕ удаляются — используются для отладки
и сравнения до завершения унификации.

Переходный мостик: source_model_line_item (FK на старый
PneumaticActuatorModelLineItem) — нужен только для резолва encoding
item-уровневых опций (safety_position / springs_qty), у которых through-модели
привязаны к старому item. После переноса through-связей на новую модель
(этап P8) поле удаляется.
"""

import importlib
import logging
import re
from decimal import Decimal
from typing import Optional

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.models import ImageGalleryMixin, TechDocMixin, EquipmentTypeMixin
from core.models.config_hash import ConfigHashMixin
from core.models.mixins import CopyMixin, TemplateMixin
from core.models.catalog_serializer import CatalogSerializerMixin
from core.utils.localization import localized_name, pick_i18n, localize_service_word
from core.models.smart_catalog_mixin import SmartCatalogMixin
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from sku.models import SKUMixin

from .pa_body import PneumaticActuatorBody
from .pa_model_line import PneumaticActuatorModelLine, PneumaticActuatorModelLineItem
from .pa_params import PneumaticActuatorVariety, PneumaticActuatorSpringsQty
from .pa_options import PneumaticTemperatureOption
from .pa_item_fields import PA_ITEM_TEMPLATE_FIELDS
from .py_options_constants import SAFETY_POSITION_NC_DEFAULT_CODE, ACTUATOR_VARIETY_RP_DEFAULT_CODE, \
    ACTUATOR_VARIETY_SY_DEFAULT_CODE, SPRINGS_DA_DEFAULT_CODE

logger = logging.getLogger(__name__)


def _fmt_num(value) -> str:
    """Отформатировать Decimal/int/float без лишних нулей (27.0 -> 27, 3.50 -> 3.5)."""
    if value is None:
        return ''
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if f == int(f):
        return str(int(f))
    return (f"{f:.2f}").rstrip('0').rstrip('.')


class PneumaticActuatorCatalogItem(
    CatalogSerializerMixin,
    ImageGalleryMixin,
    TechDocMixin,
    ConfigHashMixin,
    SKUMixin,
    CopyMixin,
    TemplateMixin,
    SmartCatalogMixin,
    EquipmentTypeMixin,
    models.Model,
):
    """
    Пневмопривод (каталожный артикул) — эталонная модель каталога.

    Базовые свойства берутся из model_line / body / variety; выбранные опции —
    прямые FK на реальные опции (как в PneumaticActuatorConstructor).
    name/description генерируются из шаблонов model_line при сохранении;
    SKU создаётся/обновляется из этой модели через SKUMixin.sync_sku().
    """

    class Origin(models.TextChoices):
        """Кто владеет жизненным циклом карточки."""
        GENERATED = 'generated', _('Сгенерирована')
        MANUAL = 'manual', _('Ручная')

    # Поля, чьи id образуют каноническую конфигурацию (порядок важен для хэша).
    config_hash_fields = (
        'model_line', 'body', 'pneumatic_actuator_variety',
        'selected_safety_position', 'selected_springs_qty',
        'selected_temperature', 'selected_ip', 'selected_exd',
        'selected_body_coating', 'selected_body_color', 'selected_manual_override',
    )

    # ── Реестр полей (единый источник правды) — pa_item_fields.py ──
    TEMPLATE_FIELDS = PA_ITEM_TEMPLATE_FIELDS

    # Серия обязана объявлять шаблоны названия/описания и артикула (catalog.W001).
    required_model_line_fields = (
        'name_template', 'description_template', 'model_item_code_template',
    )

    # Составы словарей (по ключам реестра).
    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'equipment_type', 'variety_name', 'variety_description', 'variety_code', 'body_name', 'body_code',
        'weight', 'safety_position', 'safety_position_text_value','springs_qty', 'temperature',
        'ip', 'exd', 'exd_short', 'coating', 'body_material', 'body_coating', 'body_color',
        'body_color_ral', 'body_color_name', 'manual_override', 'hand_wheel',
        # Технические характеристики (для name/description и справочника плейсхолдеров)
        'construction_name','construction_description','piston_diameter', 'turn_angle', 'turn_tuning_limit',
        'weight_spring', 'pressure_min', 'pressure_max', 'pressure',
        'air_usage_open', 'air_usage_close', 'air_usage',
        'stem_shape', 'stem_size', 'stem_size_dim',
        'max_stem_height', 'max_stem_diameter', 'stem',
        'mounting', 'thread_in', 'thread_out', 'pneumatic_conn',
        'time_open', 'time_close', 'torque_6bar',
    )

    CODE_FIELD_KEYS = (
        'code', 'springs_qty', 'temperature', 'safety_position',
        'manual_override', 'coating', 'body_color', 'ip', 'exd',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'model_line_code', 'brand_name',
        'body_name', 'body_code', 'variety_name', 'variety_code', 'weight',
        'ip', 'exd', 'exd_short',
        'body_material', 'body_coating', 'body_color_ral', 'body_color_name',
    )

    # SPEC_FIELD_KEYS закомментирован: спецификация задаётся spec_template.
    # SPEC_FIELD_KEYS = (
    #     'model_line_name', 'brand_name', 'variety_name', 'body_name', 'weight',
    # )

    # SPEC_GROUP_TITLES закомментирован: названия групп задаются в spec_template (JSON).
    # SPEC_GROUP_TITLES = {
    #     'general': 'Основные',
    # }

    name = models.TextField(
        blank=True,
        verbose_name=_("Название"),
        help_text=_('Текстовое название пневмопривода — формируется из шаблона серии'),
    )
    code = models.CharField(
        max_length=150, blank=True, null=True, verbose_name=_("Код"),
        help_text=_("Артикул пневмопривода"),
    )
    description = models.TextField(
        blank=True, verbose_name=_("Описание"),
        help_text=_('Текстовое описание пневмопривода — формируется из шаблона серии'),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    exclude_from_catalog = models.BooleanField(
        default=False,
        verbose_name=_("Не включать в каталог"),
        help_text=_("Скрыть из листингов каталога (поиск и деталка работают)"),
    )
    origin = models.CharField(
        max_length=16,
        choices=Origin.choices,
        default=Origin.GENERATED,
        verbose_name=_("Происхождение"),
        help_text=_("Кто владеет жизненным циклом карточки: генератор или человек"),
    )

    model_line = models.ForeignKey(
        PneumaticActuatorModelLine, related_name='pa_items',
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Серия"),
    )
    body = models.ForeignKey(
        PneumaticActuatorBody, related_name='pa_items',
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Корпус"),
    )
    pneumatic_actuator_variety = models.ForeignKey(
        PneumaticActuatorVariety, related_name='pa_items',
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Вид привода (DA/SR)"),
    )

    # Переходный мостик на старый model_line_item (только для encoding item-опций)
    source_model_line_item = models.ForeignKey(
        PneumaticActuatorModelLineItem, related_name='+',
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Исходная модель (legacy)"),
        help_text=_("Связь со старым model_line_item; удаляется после унификации"),
    )

    # Выбранные опции — прямые FK на реальные опции (как в Constructor)
    selected_safety_position = models.ForeignKey(
        'params.SafetyPositionOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_safety_position',
        verbose_name=_("Положение безопасности"),
    )
    selected_springs_qty = models.ForeignKey(
        PneumaticActuatorSpringsQty,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_springs_qty',
        verbose_name=_("Количество пружин"),
    )
    selected_temperature = models.ForeignKey(
        PneumaticTemperatureOption,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_temperature',
        verbose_name=_("Температурная опция"),
    )
    selected_ip = models.ForeignKey(
        'params.IpOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_ip',
        verbose_name=_("Степень защиты IP"),
    )
    selected_exd = models.ForeignKey(
        'PneumaticExdOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_exd',
        verbose_name=_("Взрывозащита"),
        help_text=_('Выбранная опция взрывозащиты (through-строка с кодировкой и видами Ex)')
    )
    selected_body_coating = models.ForeignKey(
        'PneumaticBodyDesignOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_coating',
        verbose_name=_("Исполнение корпуса"),
    )
    selected_body_color = models.ForeignKey(
        'PneumaticBodyColorOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_color',
        verbose_name=_("Цвет корпуса"),
    )
    selected_manual_override = models.ForeignKey(
        'params.HandWheelInstalledOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_hand_wheel',
        verbose_name=_("Встроенный ручной дублер"),
    )

    manual_override_option = models.ForeignKey(
        'PneumaticManualOverrideOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+',
        verbose_name=_("Опция ручного дублера"),
        help_text=_(
            'Конкретная опция ручного дублера (through) с весом mo_weight; '
            'используется для расчёта веса карточки.'
        ),
    )

    weight = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name=_("Вес, кг"),
        help_text=_(
            'Рассчитанный вес привода (корпус + пружины + ручной дублер). '
            'Материализуется при генерации карточки, а не считается динамически.'
        ),
    )

    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("Дополнительные параметры в JSON"),
    )

    # ── Фильтры каталога (по образцу старого model_line_item) ──
    FILTER_DEFINITIONS = [
        FilterDefinition(
            param_name='construction_variety_id',
            model_field='model_line__pneumatic_actuator_construction_variety',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Конструкция',
            label_i18n={'ru': 'Конструкция', 'en': 'Construction', 'cn': '结构'},
            order=1,
            mandatory='yes',
            order_by='sorting_order',
        ),
        FilterDefinition(
            param_name='actuator_variety_id',
            model_field='pneumatic_actuator_variety',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Тип привода (DA/SR)',
            label_i18n={'ru': 'Тип привода (DA/SR)', 'en': 'Actuator type (DA/SR)', 'cn': '执行器类型 (DA/SR)'},
            order=2,
            mandatory='yes',
        ),
        FilterDefinition(
            param_name='torque_nm',
            model_field='body__max_work_torque',
            filter_type=FilterType.MIN,
            data_source_type=DataSourceType.CUSTOM,
            label='Момент не менее, Нм',
            label_i18n={'ru': 'Момент не менее, Нм', 'en': 'Torque not less than, Nm', 'cn': '扭矩不小于, Nm'},
            order=3,
            mandatory='yes',
        ),
        FilterDefinition(
            param_name='work_temp_min',
            model_field='selected_temperature__work_temp_min',
            filter_type=FilterType.TEMP_MIN,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Температура, °С от',
            label_i18n={'ru': 'Температура, °С от', 'en': 'Temperature, °C from', 'cn': '温度, °C 从'},
            order=4,
        ),
        FilterDefinition(
            param_name='work_temp_max',
            model_field='selected_temperature__work_temp_max',
            filter_type=FilterType.TEMP_MAX,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Температура, °С до',
            label_i18n={'ru': 'Температура, °С до', 'en': 'Temperature, °C to', 'cn': '温度, °C 至'},
            order=5,
        ),
        FilterDefinition(
            param_name='selected_ip_id',
            model_field='selected_ip',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='IP',
            label_i18n={'ru': 'IP', 'en': 'IP', 'cn': 'IP'},
            order=6,
            order_by='sorting_order',
        ),
        FilterDefinition(
            param_name='selected_exd_id',
            model_field='selected_exd',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Взрывозащита',
            label_i18n={'ru': 'Взрывозащита', 'en': 'Explosion protection', 'cn': '防爆'},
            order=7,
            order_by='sorting_order',
        ),
        FilterDefinition(
            param_name='selected_safety_position_id',
            model_field='selected_safety_position',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Безопасное положение',
            label_i18n={'ru': 'Безопасное положение', 'en': 'Safety position', 'cn': '安全位置'},
            order=8,
            order_by='sorting_order',
        ),
        FilterDefinition(
            param_name='selected_springs_qty_id',
            model_field='selected_springs_qty',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Кол-во пружин',
            label_i18n={'ru': 'Кол-во пружин', 'en': 'Springs qty', 'cn': '弹簧数量'},
            order=9,
            order_by='sorting_order',
        ),
        FilterDefinition(
            param_name='selected_manual_override_id',
            model_field='selected_manual_override',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Ручной дублер',
            label_i18n={'ru': 'Ручной дублер', 'en': 'Manual override', 'cn': '手动超驰'},
            order=10,
            order_by='sorting_order',
        ),
    ]

    # в”Ђв”Ђ Пользовательский фильтр torque_nm (источник вЂ” таблица моментов корпуса) в”Ђв”Ђ
    @classmethod
    def _get_torque_nm_options(cls):
        """Опции фильтра «Момент не менее».

        Фронт для filter_type='gte' рендерит числовой ввод и опции НЕ использует;
        в таблице моментов ~1.5к значений — не тянем их в каждый ответ фильтров.
        """
        return []

    @classmethod
    def _apply_torque_min(cls, queryset, value):
        """Фильтр «Момент не менее, Нм»: тело подходит, если max(bto/eto/rto) >= value."""
        from decimal import Decimal, InvalidOperation
        from django.db.models import Max
        from django.db.models.functions import Greatest
        from pneumatic_actuators.models.pa_torque import BodyThrustTorqueTable
        try:
            val = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return queryset
        body_ids = (
            BodyThrustTorqueTable.objects
            .annotate(mx=Greatest('bto', 'eto', 'rto'))
            .values('body_id')
            .annotate(m=Max('mx'))
            .filter(m__gte=val)
            .values_list('body_id', flat=True)
        )
        return queryset.filter(body_id__in=list(body_ids))

    # ── Конфиг option → through-модель (для encoding в артикуле) ──
    # Через through_attr резолвится реальная опция; parent_field указывает,
    # к чему привязана through-запись (model_line или legacy model_line_item).
    _OPTION_CONFIG = {
        'selected_safety_position': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticSafetyPositionOption',
            'through_attr': 'safety_position',
            'parent_field': 'model_line_item',
        },
        'selected_springs_qty': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticSpringsQtyOption',
            'through_attr': 'springs_qty',
            'parent_field': 'model_line_item',
        },
        'selected_temperature': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticTemperatureOption',
            'through_attr': None,  # PneumaticTemperatureOption сама является опцией
            'parent_field': 'model_line',
        },
        'selected_ip': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticIpOption',
            'through_attr': 'ip_option',
            'parent_field': 'model_line',
        },
        'selected_exd': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticExdOption',
            'through_attr': None,  # PneumaticExdOption сама является опцией (кодировка + M2M видов)
            'parent_field': 'model_line',
        },
        'selected_body_coating': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticBodyDesignOption',
            'through_attr': None,  # PneumaticBodyDesignOption САМА является опцией
            'parent_field': 'model_line',
        },
        'selected_body_color': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticBodyColorOption',
            'through_attr': None,  # PneumaticBodyColorOption САМА является опцией
            'parent_field': 'model_line',
        },
        'selected_manual_override': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticManualOverrideOption',
            'through_attr': 'hand_wheel_option',
            'parent_field': 'model_line_item',
        },
    }

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Пневмопривод (каталог)')
        verbose_name_plural = _('Пневмоприводы (каталог)')

    def __str__(self):
        return self.name or self.code or f'PneumaticActuatorCatalogItem #{self.pk}'

    @classmethod
    def from_constructor(cls, constructor):
        """Собрать несохранённый item из конфигурации конструктора.

        Единый паттерн: превью/спецификация конструктора рендерятся через эту
        эталонную модель (реестр TEMPLATE_FIELDS + spec_template), а не через
        отдельный захардкоженный словарь значений.
        """
        mli = getattr(constructor, 'selected_model_line_item', None)
        manual_override = getattr(constructor, 'selected_manual_override', None)
        manual_override_option = None
        if mli and manual_override:
            from pneumatic_actuators.models.pa_options import PneumaticManualOverrideOption
            manual_override_option = PneumaticManualOverrideOption.objects.filter(
                model_line_item=mli, hand_wheel_option=manual_override,
            ).order_by('id').first()
        item = cls(
            model_line=mli.model_line if mli else None,
            body=mli.body if mli else None,
            pneumatic_actuator_variety=mli.pneumatic_actuator_variety if mli else None,
            source_model_line_item=mli,
            selected_safety_position=getattr(constructor, 'selected_safety_position', None),
            selected_springs_qty=getattr(constructor, 'selected_springs_qty', None),
            selected_temperature=getattr(constructor, 'selected_temperature', None),
            selected_ip=getattr(constructor, 'selected_ip', None),
            selected_exd=getattr(constructor, 'selected_exd', None),
            selected_body_coating=getattr(constructor, 'selected_body_coating', None),
            selected_body_color=getattr(constructor, 'selected_body_color', None),
            selected_manual_override=manual_override,
            manual_override_option=manual_override_option,
        )
        # Для превью (несохранённый item) вес считается на лету — как при генерации.
        item.weight = item.compute_weight()
        return item

    # ═══════════════════════════════════════════════════════════════
    # SKUMixin — SKU создаётся из этой модели (стандартный путь)
    # ═══════════════════════════════════════════════════════════════

    def save(self, *args, **kwargs):
        """
        Стандартный цикл каталога (единый для ручного и авто-создания):
        1. equipment_type (обязательный, PROTECT) автозаполняется из model_line;
        2. code автогенерируется из model_line.model_item_code_template, если не задан;
        3. config_hash пересчитывается из опций; коллизия → ValidationError;
        4. super().save() → TemplateMixin.save() генерирует name/description
           из шаблонов model_line (skip_auto_generate=True пропускает);
        5. sync_sku() создаёт/обновляет SKU из этой модели.

        Для ручных карточек (origin=manual) перед super().save() вес
        пересчитывается из опций (compute_weight).
        """
        if not self.equipment_type_id and self.model_line and getattr(self.model_line, 'equipment_type_id', None):
            self.equipment_type = self.model_line.equipment_type
        if not self.code:
            self.code = self.generated_model_item_code or None
        if self.manual_override_option:
            # Базовая опция дублера всегда согласована с выбранной through-опцией.
            self.selected_manual_override = self.manual_override_option.hand_wheel_option
        self.config_hash = self.compute_config_hash()
        self._check_config_hash_unique()
        if self.origin == self.Origin.MANUAL:
            # Ручная карточка: вес пересчитывается из опций при каждом сохранении.
            self.weight = self.compute_weight()
        super().save(*args, **kwargs)
        self.sync_sku()

    def clean(self):
        """Валидация: тип оборудования должен быть задан (свой или из серии)."""
        super().clean()
        if not self.equipment_type_id and not (
            self.model_line and getattr(self.model_line, 'equipment_type_id', None)
        ):
            raise ValidationError(
                _('Укажите тип оборудования или выберите серию с заданным типом оборудования')
            )
        self._check_config_hash_unique()

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — берётся из model_line."""
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        """Бренд для SKU — берётся из model_line."""
        return self.model_line.brand if self.model_line else None



    # ═══════════════════════════════════════════════════════════════
    # TemplateMixin — шаблоны названия/описания из model_line
    # ═══════════════════════════════════════════════════════════════

    def _get_name_template_source(self):
        """Шаблон названия из model_line (getattr-safe: поле появится в P4)."""
        if not self.model_line:
            return None
        return getattr(self.model_line, 'name_template', None) or None

    def _get_description_template_source(self):
        """Шаблон описания из model_line (getattr-safe: поле появится в P4)."""
        if not self.model_line:
            return None
        return getattr(self.model_line, 'description_template', None) or None

    # ═══════════════════════════════════════════════════════════════
    # Артикул: рендер model_line.model_item_code_template
    # ═══════════════════════════════════════════════════════════════

    @property
    def generated_model_item_code(self) -> str:
        """
        Артикул по шаблону model_line.model_item_code_template.
        Поддерживает плейсхолдеры {model_code} и опции; рендеринг — через
        _fill_template (единый механизм), значения encoding — из through-моделей.
        Если шаблон не задан — fallback на склейку code + encodings.
        Полный артикул = основной шаблон + « » + ext-шаблон (если задан).
        """
        template = getattr(self.model_line, 'model_item_code_template', None) if self.model_line else None
        if not template:
            return self._generate_fallback_code()

        data_dict = self._get_code_data_dict()
        result = self._fill_template(template, data_dict)

        # Очистка (как в конструкторе): двойные точки, висячие разделители, (DA), пустые скобки
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\.\s+', ' ', result)
        result = re.sub(r'\s*\(DA\)', '', result)
        result = re.sub(r'\(\s*\)', '', result)
        result = re.sub(r'-\.', '.', result)
        result = re.sub(r'\.-', '.', result)
        result = re.sub(r'\s{2,}', ' ', result)
        result = re.sub(r'[.-]+$', '', result)
        result = result.strip()

        ext = self.generated_ext_code
        if ext:
            result = f"{result} {ext}"
        return result.strip()

    @property
    def generated_ext_code(self) -> str:
        """Ext-часть артикула по шаблону model_line.ext_encoding_template.

        Плейсхолдеры те же ({model_code}, {springs_qty}, ...), значения —
        ext_encoding through-опций (фолбэк — обычный encoding/базовый код).
        Пустой шаблон — пустая строка (артикул как раньше).
        """
        template = getattr(self.model_line, 'ext_encoding_template', None) if self.model_line else None
        if not template:
            return ''
        result = self._fill_template(template, self._get_ext_code_data_dict())
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\.\s+', ' ', result)
        result = re.sub(r'\s*\(DA\)', '', result)
        result = re.sub(r'\(\s*\)', '', result)
        result = re.sub(r'-\.', '.', result)
        result = re.sub(r'\.-', '.', result)
        result = re.sub(r'\s{2,}', ' ', result)
        result = re.sub(r'[.-]+$', '', result)
        result = re.sub(r'^[.\-\s]+', '', result)
        return result.strip()

    @property
    def base_model_code(self) -> str:
        """Базовый код модели (без опций) для плейсхолдера {model_code}.

        Источник (приоритет): код/имя legacy model_line_item (мостик) → код
        корпуса. На этапе P8 базовым кодом станет собственное поле модели.
        """
        if self.source_model_line_item:
            return self.source_model_line_item.code or self.source_model_line_item.name or ''
        if self.body:
            return self.body.code or ''
        return ''

    def _generate_fallback_code(self) -> str:
        parts = [
            self.code or (self.source_model_line_item.code if self.source_model_line_item else ''),
            self.springs_qty_encoding,
            self.temperature_encoding,
            self.safety_position_encoding,
            self.manual_override_encoding,
            self.coating_encoding,
            self.ip_encoding,
            self.exd_encoding,
        ]
        return '.'.join(filter(None, parts))

    # encoding-свойства опций (для _fill_template значения берутся через getattr)
    @property
    def springs_qty_encoding(self) -> str:
        return self._get_option_encoding('selected_springs_qty')

    @property
    def springs_qty_ext_encoding(self) -> str:
        return self._get_option_ext_encoding('selected_springs_qty')

    @property
    def temperature_encoding(self) -> str:
        return self._get_option_encoding('selected_temperature')

    @property
    def temperature_ext_encoding(self) -> str:
        return self._get_option_ext_encoding('selected_temperature')

    @property
    def safety_position_encoding(self) -> str:
        return self._get_option_encoding('selected_safety_position')

    @property
    def safety_position_ext_encoding(self) -> str:
        return self._get_option_ext_encoding('selected_safety_position')

    @property
    def safety_position_text_value(self) -> str:
        return self.selected_safety_position

    @property
    def manual_override_encoding(self) -> str:
        return self._get_option_encoding('selected_manual_override')

    @property
    def manual_override_ext_encoding(self) -> str:
        return self._get_option_ext_encoding('selected_manual_override')

    @property
    def coating_encoding(self) -> str:
        return self._get_option_encoding('selected_body_coating')

    @property
    def coating_ext_encoding(self) -> str:
        return self._get_option_ext_encoding('selected_body_coating')

    @property
    def body_color_encoding(self) -> str:
        return self._get_option_encoding('selected_body_color')

    @property
    def body_color_ext_encoding(self) -> str:
        return self._get_option_ext_encoding('selected_body_color')

    def _res_body_coating(self, locale=None) -> str:
        """Локализованное покрытие корпуса (JSON body_coating → справочник)."""
        opt = self.selected_body_coating
        if not opt:
            return ''
        if opt.body_coating:
            return pick_i18n(opt.body_coating, locale) or ''
        return localized_name(opt.body_coating_option, locale) if opt.body_coating_option else ''

    def _res_exd_short(self, locale=None) -> str:
        """Короткая строка взрывозащиты из prefetched M2M.

        Дублирует логику ``PneumaticExdOption.get_exd_short_list``, но читает
        ``exd_options.all()`` напрямую (prefetch-кэш) вместо ``get_exd_options()``,
        чтобы в списках не порождать N+1 запросов.
        """
        exd = self.selected_exd
        if not exd:
            return ''
        seen = set()
        result = []
        for o in exd.exd_options.all():
            ec = o.explosion_protection_class
            if ec is None:
                continue
            name = str(ec)
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        if not result:
            for o in exd.exd_options.all():
                if o.exd_full_code and o.exd_full_code not in result:
                    result.append(o.exd_full_code)
        return ' / '.join(result)

    def _res_weight(self, locale=None) -> str:
        """Вес без лишних нулей (19.500 → 19.5)."""
        return _fmt_num(self.weight)

    @property
    def ip_encoding(self) -> str:
        return self._get_option_encoding('selected_ip')

    @property
    def ip_ext_encoding(self) -> str:
        return self._get_option_ext_encoding('selected_ip')

    @property
    def exd_encoding(self) -> str:
        return self._get_option_encoding('selected_exd')

    @property
    def exd_ext_encoding(self) -> str:
        return self._get_option_ext_encoding('selected_exd')

    def _get_option_encoding(self, field_name: str) -> str:
        """
        Encoding опции из through-модели (не code реальной опции!).
        Для item-уровневых опций (safety/springs) through-запись привязана
        к legacy model_line_item — резолвим через source_model_line_item;
        без мостика — fallback на code реальной опции.
        """
        config = self._OPTION_CONFIG.get(field_name)
        if not config:
            return ''
        option_value = getattr(self, field_name)
        if not option_value:
            return ''

        through_attr = config.get('through_attr')
        if through_attr is None:
            # Temperature: through-модель сама является опцией
            return getattr(option_value, 'encoding', '') or ''

        parent_field = config.get('parent_field')
        if parent_field == 'model_line':
            parent_obj = self.model_line
        elif parent_field == 'model_line_item':
            parent_obj = self.source_model_line_item
        else:
            parent_obj = None

        if not parent_obj:
            return getattr(option_value, 'code', '') or ''

        through_model = self._import_through_model(config)
        try:
            through_instance = through_model.objects.filter(
                **{f'{through_attr}_id': option_value.id, parent_field: parent_obj}
            ).first()
        except Exception as e:
            logger.error(f"Ошибка поиска encoding {field_name}: {e}")
            return ''
        if through_instance is not None:
            # through-строка найдена: возвращаем её encoding (пустой остаётся пустым,
            # не подменяем кодом реальной опции).
            return through_instance.encoding or ''
        # through-записи нет — fallback на code реальной опции.
        return getattr(option_value, 'code', '') or ''

    def _get_option_ext_encoding(self, field_name: str) -> str:
        """
        Ext-encoding опции из through-модели (парно _get_option_encoding).
        Пустое ext_encoding — пустая строка (опция не участвует в ext-части);
        through-записи нет — пустая строка (не fallback на code реальной опции:
        ext-кодировка задаётся только явно в through-строке).
        """
        config = self._OPTION_CONFIG.get(field_name)
        if not config:
            return ''
        option_value = getattr(self, field_name)
        if not option_value:
            return ''

        through_attr = config.get('through_attr')
        if through_attr is None:
            # Temperature/design/color/exd: through-модель сама является опцией
            return getattr(option_value, 'ext_encoding', '') or ''

        parent_field = config.get('parent_field')
        if parent_field == 'model_line':
            parent_obj = self.model_line
        elif parent_field == 'model_line_item':
            parent_obj = self.source_model_line_item
        else:
            parent_obj = None

        if not parent_obj:
            return ''

        through_model = self._import_through_model(config)
        try:
            through_instance = through_model.objects.filter(
                **{f'{through_attr}_id': option_value.id, parent_field: parent_obj}
            ).first()
        except Exception as e:
            logger.error(f"Ошибка поиска ext_encoding {field_name}: {e}")
            return ''
        if through_instance is not None:
            return through_instance.ext_encoding or ''
        return ''

    @classmethod
    def _import_through_model(cls, config: dict):
        """Импорт through-модели по пути из конфига."""
        module_name, class_name = config['through_model_path'].rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    # ═══════════════════════════════════════════════════════════════
    # Расчётные свойства
    # ═══════════════════════════════════════════════════════════════

    def compute_weight(self) -> Optional[Decimal]:
        """Рассчитать вес привода (корпус + пружины + ручной дублер), кг.

        Используется при материализации карточек; результат сохраняется в поле
        ``weight``, чтобы при отображении не пересчитывать вес динамически.
        """
        from .pa_weight import calculate_actuator_weight, resolve_manual_override_weight
        variety = self.pneumatic_actuator_variety
        springs = self.selected_springs_qty
        mo = self.manual_override_option
        manual_override_weight = (
            mo.mo_weight if mo else
            resolve_manual_override_weight(
                self.source_model_line_item, self.selected_manual_override)
        )
        return calculate_actuator_weight(
            self.body,
            variety.code if variety else None,
            springs.code if springs else None,
            manual_override_weight=manual_override_weight,
        )

    @property
    def calculated_weight(self) -> Optional[float]:
        """Сохранённый вес карточки (материализован при генерации)."""
        return float(self.weight) if self.weight is not None else None

    # ═══════════════════════════════════════════════════════════════
    # Resolver'ы для spec_template (технические + таблица моментов)
    # ═══════════════════════════════════════════════════════════════

    def _res_pressure(self) -> str:
        body = self.body
        if body and body.min_pressure_bar is not None:
            return f"{_fmt_num(body.min_pressure_bar)} - {_fmt_num(body.max_pressure_bar)} бар"
        return ''

    def _res_air_usage(self, locale=None) -> str:
        body = self.body
        if not body:
            return ''
        open_v = _fmt_num(body.air_usage_open)
        close_v = _fmt_num(body.air_usage_close)
        if not (open_v or close_v):
            return ''
        open_word = localize_service_word('открытие', locale)
        close_word = localize_service_word('закрытие', locale)
        return f"{open_word} {open_v}, {close_word} {close_v}"

    def _res_pneumatic_conn(self, locale=None) -> str:
        body = self.body
        if body and body.pneumatic_connection.exists():
            names = [localized_name(c, locale) for c in body.pneumatic_connection.all()]
            return localize_service_word(' или ', locale).join(names)
        return ''

    def _res_piston_diameter(self) -> str:
        body = self.body
        if body and body.piston_diameter is not None:
            return f"{_fmt_num(body.piston_diameter)} мм"
        return ''

    def _res_weight_spring(self) -> str:
        body = self.body
        if body and body.weight_spring is not None:
            return f"{_fmt_num(body.weight_spring)} кг"
        return ''

    def _res_pressure_min(self) -> str:
        body = self.body
        if body and body.min_pressure_bar is not None:
            return f"{_fmt_num(body.min_pressure_bar)} бар"
        return ''

    def _res_pressure_max(self) -> str:
        body = self.body
        if body and body.max_pressure_bar is not None:
            return f"{_fmt_num(body.max_pressure_bar)} бар"
        return ''

    def _res_air_usage_open(self) -> str:
        body = self.body
        if body and body.air_usage_open is not None:
            return f"{_fmt_num(body.air_usage_open)}"
        return ''

    def _res_air_usage_close(self) -> str:
        body = self.body
        if body and body.air_usage_close is not None:
            return f"{_fmt_num(body.air_usage_close)}"
        return ''

    def _res_max_stem_height(self) -> str:
        body = self.body
        if body and body.max_stem_height is not None:
            return f"{_fmt_num(body.max_stem_height)} мм"
        return ''

    def _res_max_stem_diameter(self) -> str:
        body = self.body
        if body and body.max_stem_diameter is not None:
            return f"{_fmt_num(body.max_stem_diameter)} мм"
        return ''

    def _res_stem_size_dim(self) -> str:
        """Габарит штока: для квадрата — «27×27», для вала со шпонкой — «16×5»."""
        body = self.body
        if not body or not body.stem_size:
            return ''
        ss = body.stem_size
        d = _fmt_num(ss.stem_diameter)
        stem_code = (ss.stem_type.code if ss.stem_type else '') or ''
        if stem_code == 'sq':
            return f"{d}×{d}" if d else (ss.name or '')
        key = _fmt_num(ss.chunk_x)
        if d and key:
            return f"{d}×{key}"
        return ss.name or ''

    def _res_torque_table(self, locale=None):
        """HTML-блок таблицы моментов/усилий по выбранной конфигурации (DA или пружины SR)."""
        body = self.body
        if not body:
            return ''
        from pneumatic_actuators.models import BodyThrustTorqueTable
        ncno_code = self.selected_safety_position.code if self.selected_safety_position else SAFETY_POSITION_NC_DEFAULT_CODE
        construction_variety = self.model_line.pneumatic_actuator_construction_variety if self.model_line else None
        construction_variety_code = construction_variety.code if construction_variety else ACTUATOR_VARIETY_RP_DEFAULT_CODE
        da_sr_code = self.pneumatic_actuator_variety.code if self.pneumatic_actuator_variety else None
        spring_qty = self.selected_springs_qty
        if not spring_qty and da_sr_code == SPRINGS_DA_DEFAULT_CODE:
            # DA: пружин нет — берём DA-опцию, чтобы таблица показала только строку DA.
            spring_qty = PneumaticActuatorSpringsQty.objects.filter(code=SPRINGS_DA_DEFAULT_CODE).first()
        torque_data = BodyThrustTorqueTable.get_torque_thrust_values(
            current_body=body,
            spring_qty_list=[spring_qty] if spring_qty else None,
            ncno_code=ncno_code,
            construction_variety_code=construction_variety_code,
            da_sr_code=da_sr_code,
        )
        # Точной комбинации (тело+пружина) нет в БД — показываем все строки тела
        # (прежнее поведение до выбора пружины; данные заполняет пользователь).
        # При ошибке источника данных фолбэк не делаем (не маскируем сбой).
        if (spring_qty and 'error' not in torque_data
                and not torque_data.get('data', {}).get('by_spring')):
            torque_data = BodyThrustTorqueTable.get_torque_thrust_values(
                current_body=body,
                ncno_code=ncno_code,
                construction_variety_code=construction_variety_code,
                da_sr_code=da_sr_code,
            )
            # В данных только DA-строки (модель работает только в DA) — показываем
            # таблицу как DA-вариант: без колонки пружин, одна колонка на давление.
            springs = torque_data.get('table_config', {}).get('spring_order', [])
            if springs and set(springs) == {SPRINGS_DA_DEFAULT_CODE}:
                torque_data = BodyThrustTorqueTable.get_torque_thrust_values(
                    current_body=body,
                    ncno_code=ncno_code,
                    construction_variety_code=construction_variety_code,
                    da_sr_code=SPRINGS_DA_DEFAULT_CODE,
                )
        html = BodyThrustTorqueTable.format_for_html(torque_data, locale=locale or 'ru')
        return {'__html': html} if html else ''

    @staticmethod
    def _da_torque_pair(bto, eto):
        """DA: если задан только один из BTO/ETO (второй 0) — второй равен ненулевому."""
        b = float(bto or 0)
        e = float(eto or 0)
        if b and not e:
            e = b
        elif e and not b:
            b = e
        return {'bto': b, 'eto': e}

    def _res_torque_6bar(self, locale=None) -> str:
        """Момент при 6 бар из таблицы моментов по правилам формирования таблицы.

        DA — только воздух (AIR: BTO/ETO); SR шестерня-рейка — воздух + пружины
        (AIR/SPR: BTO/ETO); SR кулисный — воздух + пружины (AIR/SPR: BTO/RTO/ETO).
        Для НО подписи инвертируются (BTC/ETC/RTC), как в таблице моментов.
        """
        body = self.body
        if not body:
            return ''
        from params.models import PneumaticAirSupplyPressure
        from pneumatic_actuators.models import BodyThrustTorqueTable

        ncno_code = self.selected_safety_position.code if self.selected_safety_position else SAFETY_POSITION_NC_DEFAULT_CODE
        construction_variety = self.model_line.pneumatic_actuator_construction_variety if self.model_line else None
        construction_code = construction_variety.code if construction_variety else ACTUATOR_VARIETY_RP_DEFAULT_CODE
        variety_code = self.pneumatic_actuator_variety.code if self.pneumatic_actuator_variety else None
        is_da = variety_code == SPRINGS_DA_DEFAULT_CODE

        spring_qty = self.selected_springs_qty
        if not spring_qty and is_da:
            # DA: пружин нет — берём DA-опцию, как в _res_torque_table.
            spring_qty = PneumaticActuatorSpringsQty.objects.filter(code=SPRINGS_DA_DEFAULT_CODE).first()

        nc = ncno_code == SAFETY_POSITION_NC_DEFAULT_CODE
        if is_da:
            fields = [('bto', 'BTO' if nc else 'BTC'), ('eto', 'ETO' if nc else 'ETC')]
        elif construction_code == ACTUATOR_VARIETY_RP_DEFAULT_CODE:
            fields = [('bto', 'BTO' if nc else 'BTC'), ('eto', 'ETO' if nc else 'ETC')]
        elif construction_code == ACTUATOR_VARIETY_SY_DEFAULT_CODE:
            fields = [('bto', 'BTO' if nc else 'BTC'), ('rto', 'RTO' if nc else 'RTC'),
                      ('eto', 'ETO' if nc else 'ETC')]
        else:
            fields = [('bto', 'BTO' if nc else 'BTC'), ('rto', 'RTO' if nc else 'RTC'),
                      ('eto', 'ETO' if nc else 'ETC')]

        pressure_6 = PneumaticAirSupplyPressure.objects.filter(pressure_bar=6).first()
        if pressure_6 is None:
            return ''
        spring_pressure = PneumaticAirSupplyPressure.objects.filter(code='spring').first()

        base = BodyThrustTorqueTable.objects.filter(body=body)
        air_rows = list(base.filter(pressure=pressure_6, spring_qty=spring_qty)) if spring_qty else []
        spr_rows = (
            list(base.filter(pressure=spring_pressure, spring_qty=spring_qty))
            if spring_pressure is not None and spring_qty is not None and not is_da
            else []
        )

        # Фолбэк как у таблицы моментов: строк по выбранной пружине нет — берём
        # первую пружину тела при 6 бар. Тела бывают только-DA и только-SR,
        # поэтому фолбэк ограничен типом привода: DA — только DA-строки
        # (пружинной части у DA не бывает), SR — только пружинные строки.
        if not air_rows and not spr_rows:
            fallback_qs = PneumaticActuatorSpringsQty.objects.filter(
                body_thrust_torque_table__body=body,
                body_thrust_torque_table__pressure=pressure_6,
            )
            if is_da:
                fallback_qs = fallback_qs.filter(code=SPRINGS_DA_DEFAULT_CODE)
            else:
                fallback_qs = fallback_qs.exclude(code=SPRINGS_DA_DEFAULT_CODE)
            fallback = fallback_qs.order_by('sorting_order').first()
            if fallback is not None:
                air_rows = list(base.filter(pressure=pressure_6, spring_qty=fallback))
                if not is_da and spring_pressure is not None:
                    spr_rows = list(base.filter(pressure=spring_pressure, spring_qty=fallback))

        fmt = BodyThrustTorqueTable.format_torque_value
        parts = []
        for prefix, rows in (('AIR', air_rows), ('SPR', spr_rows)):
            if not rows:
                continue
            row = rows[0]
            if is_da:
                # DA: если задан только один из BTO/ETO (второй 0) — второй равен ненулевому.
                pair = self._da_torque_pair(row.bto, row.eto)
            values = []
            for field_name, label in fields:
                value = pair.get(field_name) if is_da else getattr(row, field_name, None)
                values.append(f'{label} {fmt(value)}' if value is not None else f'{label} —')
            parts.append(f'{prefix}: ' + ' / '.join(values))
        return '; '.join(parts)

    def _get_valve_torque_nm(self) -> float:
        """Момент на арматуре (Нм) для расчёта времени открытия/закрытия.

        0 — момент не задан (служебная функция считает базовое время без учёта
        сопротивления арматуры). Если задан в ``extra_params`` — время увеличивается
        за счёт эквивалентного падения давления.
        """
        params = self.extra_params or {}
        for key in ('valve_torque_nm', 'valve_torque', 'required_torque_nm'):
            raw = params.get(key)
            if raw in (None, ''):
                continue
            try:
                return float(raw)
            except (TypeError, ValueError):
                continue
        return 0.0

    def _res_time_open(self) -> str:
        return self._res_time_value('time_open')

    def _res_time_close(self) -> str:
        return self._res_time_value('time_close')

    def _res_time_value(self, key: str) -> str:
        """Время открытия/закрытия через служебную функцию PneumaticCloseTimeParameter."""
        from pneumatic_actuators.models import PneumaticCloseTimeParameter

        if not self.body_id:
            return ''
        try:
            result = PneumaticCloseTimeParameter.get_time_to_close(
                self.body_id,
                self.selected_springs_qty,
                pressure=None,
                valve_torque_nm=self._get_valve_torque_nm(),
            )
        except Exception:
            logger.exception('Не удалось рассчитать время %s', key)
            return ''
        if not isinstance(result, dict):
            return ''
        value = result.get(key)
        if value is None:
            return ''
        try:
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return str(value)

    def render_spec_html(self, locale=None) -> str:
        """HTML-описание спецификации для модалки «Просмотр спецификации».

        Строится из ``_get_spec_sections()`` — того же источника, что и вкладка
        «Характеристики» (``spec_template`` серия → EquipmentType). Значение поля
        может быть строкой или ``{'__html': ...}`` (таблица моментов) — HTML-блок
        вставляется как есть.
        """
        from html import escape

        sections = self._get_spec_sections(locale=locale)
        if not sections:
            return ''

        parts = []
        for group_title, fields in sections.items():
            if not fields:
                continue
            parts.append(
                f'<h4 style="margin:14px 0 6px;font-size:14px;">'
                f'{escape(str(group_title))}</h4>'
            )
            parts.append(
                '<table style="border-collapse:collapse;width:100%;font-size:13px;">'
            )
            for label, value in fields.items():
                if isinstance(value, dict) and value.get('__html'):
                    parts.append(
                        f'<tr><td colspan="2" style="padding:6px 0;">'
                        f'{value["__html"]}</td></tr>'
                    )
                else:
                    text = str(value) if value not in (None, '') else '—'
                    parts.append(
                        f'<tr><td style="padding:3px 12px 3px 0;color:#6b7280;'
                        f'white-space:nowrap;vertical-align:top;">{escape(str(label))}</td>'
                        f'<td style="padding:3px 0;vertical-align:top;">{escape(text)}</td></tr>'
                    )
            parts.append('</table>')
        return ''.join(parts)

    # ═══════════════════════════════════════════════════════════════
    # CatalogSerializerMixin — галерея с fallback на изображения серии
    # ═══════════════════════════════════════════════════════════════

    def _get_images_section(self):
        """Изображения: сначала item, затем model_line (единый паттерн БКВ)."""
        from_item = super()._get_images_section()
        if from_item:
            return from_item
        ml = self.model_line
        if ml and hasattr(ml, '_get_images_section'):
            return ml._get_images_section()
        return []

    def _get_list_preview_images(self):
        """Одно изображение для сетки результатов (preview_url/url/thumb_url).

        Рассчитывается из префетченных image_gallery__items__image__variants —
        без доп. запросов к БД. Для списка из десятков карточек это убирает сотни
        запросов по вариантам изображений (каждый _get_images_section ранее
        дёргал variants несколькими .filter().first()).
        """
        g = self._gallery
        if not g:
            return []
        items = list(g.items.all())
        if not items:
            return []
        gallery_item = next((i for i in items if i.is_default), items[0])
        img = gallery_item.image
        if not img:
            return []

        variants = list(img.variants.all())

        def find(role, width=None):
            for v in variants:
                if v.role == role and (width is None or v.width == width):
                    return v
            return None

        from storage_manager.services import file_service
        card800 = find('card', 800)
        card400 = find('card', 400)
        thumb150 = find('thumb', 150)
        thumb80 = find('thumb', 80)
        icon50 = find('icon', 50)

        url = ''
        if card800:
            url = file_service.get_file_url(card800.file_path)
        elif card400:
            url = file_service.get_file_url(card400.file_path)
        elif img.media_file:
            url = img.media_file.url

        preview_v = card400 or thumb150 or icon50
        if not preview_v:
            candidates = [v for v in variants if v.role in ('card', 'thumb', 'icon', 'page')]
            if candidates:
                preview_v = min(candidates, key=lambda v: v.width)
        preview = (file_service.get_file_url(preview_v.file_path) if preview_v
                   else (img.media_file.url if img.media_file else ''))

        thumb = ''
        if thumb150:
            thumb = file_service.get_file_url(thumb150.file_path)
        elif thumb80:
            thumb = file_service.get_file_url(thumb80.file_path)
        else:
            thumb = preview or url

        return [{
            'id': img.id,
            'url': url,
            'preview_url': preview,
            'thumb_url': thumb,
        }]
