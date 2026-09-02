# pneumatic_actuators/models/pa_item.py
"""
ЭТАЛОННАЯ каталожная модель пневмопривода — PneumaticActuatorItem.

Создана 2026-08-31 в рамках унификации каталогов. Работает по общему контракту
(как DirectionValve / LimitSwitchBox / FilterRegulator / GearBox / PneumaticFitting):

- Шаблоны name_template / description_template живут на model_line
  (PneumaticActuatorModelLine, поля добавляются отдельным шагом);
- Item переопределяет _get_name_template_source / _get_description_template_source
  → model_line, _get_default_* (fallback) и _get_data_dict (плейсхолдер → путь);
- Автогенерация name/description — в TemplateMixin.save()
  (пропускается флагом skip_auto_generate=True);
- save() = super().save() + sync_sku() — SKU создаётся из ЭТОЙ модели
  через SKUMixin (стандартный путь, как в остальных каталогах);
- Артикул (code) рендерится из model_line.model_item_code_template
  через _fill_template + _get_code_data_dict (encoding опций из through-моделей).

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
from typing import Dict, Any, Optional

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.models import ImageGalleryMixin, TechDocMixin, EquipmentTypeMixin
from core.models.mixins import CopyMixin, TemplateMixin, CatalogDictMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from sku.models import SKUMixin

from .pa_body import PneumaticActuatorBody
from .pa_model_line import PneumaticActuatorModelLine, PneumaticActuatorModelLineItem
from .pa_params import PneumaticActuatorVariety, PneumaticActuatorSpringsQty
from .pa_options import PneumaticTemperatureOption

logger = logging.getLogger(__name__)


class PneumaticActuatorItem(
    CatalogDictMixin,
    ImageGalleryMixin,
    TechDocMixin,
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
        'params.ExdOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_exd',
        verbose_name=_("Взрывозащита"),
    )
    selected_body_coating = models.ForeignKey(
        'params.BodyCoatingOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_coating',
        verbose_name=_("Покрытие корпуса"),
    )
    selected_hand_wheel = models.ForeignKey(
        'params.HandWheelInstalledOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_items_hand_wheel',
        verbose_name=_("Встроенный ручной дублер"),
    )

    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("Дополнительные параметры в JSON"),
    )

    # ── Фильтры каталога (по образцу старого model_line_item) ──
    FILTER_DEFINITIONS = [
        FilterDefinition(
            param_name='actuator_variety_id',
            model_field='pneumatic_actuator_variety',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Тип привода (DA/SR)',
            order=1,
            mandatory='yes',
        ),
        FilterDefinition(
            param_name='torque_nm',
            model_field='body__max_work_torque',
            filter_type=FilterType.MIN,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Момент не менее, Нм',
            order=2,
            mandatory='yes',
        ),
    ]

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
            'through_attr': 'exd_option',
            'parent_field': 'model_line',
        },
        'selected_body_coating': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticBodyCoatingOption',
            'through_attr': 'body_coating_option',
            'parent_field': 'model_line',
        },
        'selected_hand_wheel': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticHandWheelOption',
            'through_attr': 'hand_wheel_option',
            'parent_field': 'model_line',
        },
    }

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Пневмопривод (каталог)')
        verbose_name_plural = _('Пневмоприводы (каталог)')

    def __str__(self):
        return self.name or self.code or f'PneumaticActuatorItem #{self.pk}'

    # ═══════════════════════════════════════════════════════════════
    # SKUMixin — SKU создаётся из этой модели (стандартный путь)
    # ═══════════════════════════════════════════════════════════════

    def save(self, *args, **kwargs):
        """
        Стандартный цикл каталога:
        1. equipment_type (обязательный, PROTECT) автозаполняется из model_line;
        2. code автогенерируется из model_line.model_item_code_template, если не задан;
        3. super().save() → TemplateMixin.save() генерирует name/description
           из шаблонов model_line (skip_auto_generate=True пропускает);
        4. sync_sku() создаёт/обновляет SKU из этой модели.
        """
        if not self.equipment_type_id and self.model_line and getattr(self.model_line, 'equipment_type_id', None):
            self.equipment_type = self.model_line.equipment_type
        if not self.code:
            self.code = self.generated_model_item_code or None
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

    def _get_default_name_template(self) -> str:
        return (
            "{model_code} Пневмопривод {brand} {variety}; "
            "{safety_position}; {springs_qty}; "
            "Т.исп. {temperature}; {ip}; {exd}; "
            "Покрытие корпуса: {coating}; Ручной дублер: {hand_wheel}"
        )

    def _get_default_description_template(self) -> str:
        return (
            "{model_code} Пневмопривод {brand} {variety}; "
            "Положение безопасности: {safety_position}; "
            "Количество пружин: {springs_qty}; "
            "Т.исп. {temperature}; {ip}; {exd}; "
            "Покрытие корпуса: {coating}; "
            "Ручной дублер на корпусе: {hand_wheel}; "
            "Вес {weight} кг"
        )

    def _get_data_dict(self) -> Dict[str, str]:
        """Словарь плейсхолдер → путь (для TemplateMixin)."""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{variety}': 'pneumatic_actuator_variety',
            '{body_code}': 'body__code',
            '{body_name}': 'body__name',
            '{safety_position}': 'selected_safety_position',
            '{springs_qty}': 'selected_springs_qty',
            '{temperature}': 'selected_temperature',
            '{ip}': 'selected_ip',
            '{exd}': 'selected_exd',
            '{coating}': 'selected_body_coating',
            '{hand_wheel}': 'selected_hand_wheel',
            '{weight}': 'calculated_weight',
        }

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
        """
        template = getattr(self.model_line, 'model_item_code_template', None) if self.model_line else None
        if not template:
            return self._generate_fallback_code()

        data_dict = self._get_code_data_dict()
        result = self._fill_template(template, data_dict)

        # Очистка (как в конструкторе): двойные точки, висячие разделители, (DA)
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\.\s+', ' ', result)
        result = re.sub(r'\s*\(DA\)', '', result)
        return result.strip('. ')

    def _get_code_data_dict(self) -> Dict[str, str]:
        """Плейсхолдер артикула → имя @property/поля с encoding."""
        return {
            '{model_code}': 'base_model_code',
            '{springs_qty}': 'springs_qty_encoding',
            '{temperature}': 'temperature_encoding',
            '{safety_position}': 'safety_position_encoding',
            '{hand_wheel}': 'hand_wheel_encoding',
            '{coating}': 'coating_encoding',
            '{ip}': 'ip_encoding',
            '{exd}': 'exd_encoding',
        }

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
            self.hand_wheel_encoding,
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
    def temperature_encoding(self) -> str:
        return self._get_option_encoding('selected_temperature')

    @property
    def safety_position_encoding(self) -> str:
        return self._get_option_encoding('selected_safety_position')

    @property
    def hand_wheel_encoding(self) -> str:
        return self._get_option_encoding('selected_hand_wheel')

    @property
    def coating_encoding(self) -> str:
        return self._get_option_encoding('selected_body_coating')

    @property
    def ip_encoding(self) -> str:
        return self._get_option_encoding('selected_ip')

    @property
    def exd_encoding(self) -> str:
        return self._get_option_encoding('selected_exd')

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
        if through_instance and through_instance.encoding:
            return through_instance.encoding
        # through-записи нет (или без encoding) — fallback на code реальной опции
        return getattr(option_value, 'code', '') or ''

    @classmethod
    def _import_through_model(cls, config: dict):
        """Импорт through-модели по пути из конфига."""
        module_name, class_name = config['through_model_path'].rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    # ═══════════════════════════════════════════════════════════════
    # Расчётные свойства
    # ═══════════════════════════════════════════════════════════════

    @property
    def calculated_weight(self) -> Optional[float]:
        """Вес: базовый вес корпуса (weight_spring); уточняется на этапе P8."""
        if not self.body:
            return None
        weight = getattr(self.body, 'weight_spring', None)
        if weight is None:
            return None
        try:
            return float(weight)
        except (TypeError, ValueError):
            return None

    # ═══════════════════════════════════════════════════════════════
    # CatalogDictMixin — сериализация для карточки каталога
    # ═══════════════════════════════════════════════════════════════

    def _get_template_vars(self) -> Dict[str, str]:
        """Плоский словарь строковых значений для UI и шаблонов."""
        body = self.body
        ml = self.model_line
        variety = self.pneumatic_actuator_variety
        return {
            'code': self.code or '',
            'name': self.name or '',
            'model_line_name': ml.name if ml else '',
            'model_line_code': ml.code if ml else '',
            'brand_name': ml.brand.name if ml and ml.brand else '',
            'body_name': body.name if body else '',
            'body_code': body.code if body else '',
            'variety_name': variety.name if variety else '',
            'variety_code': variety.code if variety else '',
            'weight': str(self.calculated_weight) if self.calculated_weight is not None else '',
        }

    def _get_model_line_summary(self) -> dict:
        ml = self.model_line
        if not ml:
            return None
        return {
            'id': ml.id,
            'name': ml.name,
            'code': ml.code or '',
            'description': ml.description or '',
            'brand': {'id': ml.brand.id, 'name': ml.brand.name} if ml.brand else None,
        }

    def _get_sku_summary(self) -> dict:
        """SKU — реальная запись (SKUMixin.sync_sku)."""
        if not self.sku:
            return None
        return {'id': self.sku.id, 'code': self.sku.code, 'name': self.sku.name}

    def _get_ml_images(self):
        """Изображения: сначала item, затем model_line (единый паттерн БКВ)."""
        from_item = self._get_images_section() if hasattr(self, '_get_images_section') else []
        if from_item:
            return from_item
        ml = self.model_line
        if ml and hasattr(ml, '_get_images_section'):
            return ml._get_images_section()
        return []

    def _get_ml_docs(self):
        return self._get_docs_section() if hasattr(self, '_get_docs_section') else []

    def _get_ml_certs(self):
        return self._get_certs_section() if hasattr(self, '_get_certs_section') else []

    def to_dict(self) -> Dict[str, Any]:
        """Структурированная сериализация для карточки каталога."""
        tv = self._get_template_vars()
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title(),
            'description': self.generate_description(),
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
            'template_vars': tv,
            'sections': [
                {
                    'key': 'images', 'title': 'Изображения', 'type': 'gallery',
                    'order': 0, 'data': self._get_ml_images(),
                },
                {
                    'key': 'specs', 'title': 'Характеристики', 'type': 'specs',
                    'order': 1, 'groups': [
                        {
                            'key': 'general', 'title': 'Основные', 'order': 1,
                            'fields': [
                                {'key': 'model_line_name', 'label': 'Серия', 'value': tv['model_line_name'], 'type': 'text', 'order': 1},
                                {'key': 'brand_name', 'label': 'Бренд', 'value': tv['brand_name'], 'type': 'text', 'order': 2},
                                {'key': 'variety_name', 'label': 'Тип привода', 'value': tv['variety_name'], 'type': 'text', 'order': 3},
                                {'key': 'body_name', 'label': 'Корпус', 'value': tv['body_name'], 'type': 'text', 'order': 4},
                                {'key': 'weight', 'label': 'Вес (кг)', 'value': tv['weight'], 'type': 'number', 'order': 6},
                            ],
                        },
                    ],
                },
                {
                    'key': 'docs', 'title': 'Документация', 'type': 'files',
                    'order': 2, 'data': self._get_ml_docs(),
                },
                {
                    'key': 'certs', 'title': 'Сертификаты', 'type': 'files',
                    'order': 3, 'data': self._get_ml_certs(),
                },
                {
                    'key': 'description', 'title': 'Описание', 'type': 'text',
                    'order': 4, 'data': self.description or '',
                },
            ],
        }

    def to_values_dict(self) -> dict:
        """Облегчённая сериализация для списков каталога."""
        tv = self._get_template_vars()
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title() or self.name or '',
            'template_vars': tv,
            'values': tv,
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
        }
