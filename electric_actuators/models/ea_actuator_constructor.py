# electric_actuators/models/ea_actuator_constructor.py
"""
Конструктор электропривода — пошаговый выбор модели и опций через прямые FK.

## Архитектура
FK указывают напрямую на реальные опции (params.IpOption, params.ExdOption, ...).
Доступность опций проверяется через through-модели из ea_options / ea_model_line_item_options —
они хранят связи «model_line → доступная опция» и «model_line_item → доступная опция».

## Поток работы
1. Выбор серии (selected_model_line) → фильтруются model_line_items
2. Выбор модели (selected_model_line_item) → загружаются доступные опции
3. Опции автозаполняются дефолтами через through-модели
4. save() генерирует name/code/description, проверяет дубликаты

## Генерация кода
encoding для кода берётся из through-моделей (не code реальных опций!).
_get_option_encoding() находит through-запись по ID опции + родителю.
Шаблон артикула — model_line.model_item_code_template.

## API
- ConstructorViewSet: CRUD + model_lines + model_line_items + options + preview
- /preview/ — генерирует код и описание без сохранения в базу
- /{id}/options/ — список доступных опций для выбранной модели
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

import importlib
from typing import List, Optional, Any, Dict
import re

import logging

logger = logging.getLogger(__name__)


class ElectricActuatorConstructor(models.Model):
    """
    Конструктор электропривода — пошаговый выбор модели и опций через прямые FK.

    В отличие от старой версии (through-модели как FK), здесь FK указывают
    напрямую на реальные опции (params.IpOption, params.ExdOption, ...).
    Доступность опций проверяется через through-модели.
    """

    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название привода - формируется автоматически'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код привода - формируется автоматически"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание привода - формируется автоматически'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    # Шаг 1: выбор серии (model_line)
    selected_model_line = models.ForeignKey(
        'electric_actuators.ElectricActuatorModelLine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='constructor_model_lines',
        verbose_name=_('Серия'),
        help_text=_('Серия электроприводов — фильтрует доступные модели')
    )

    # Шаг 2: выбор конкретной модели (model_line_item)
    selected_model_line_item = models.ForeignKey(
        'electric_actuators.ElectricActuatorModelLineItem',
        related_name='constructor_model_line_items',
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_('Модель'),
        help_text=_('Модель электропривода')
    )

    # --- Конструктивные особенности ---
    actual_mounting_plate = models.ForeignKey(
        'params.MountingPlateTypes',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constructor_mounting_plate',
        verbose_name=_('Монтажная площадка'),
        help_text=_('Монтажная площадка')
    )
    actual_stem_shape = models.ForeignKey(
        'params.StemShapes',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constructor_stem_shape',
        verbose_name=_('Тип отверстия под шток'),
        help_text=_('Тип отверстия под шток арматуры')
    )
    actual_stem_size = models.ForeignKey(
        'params.StemSize',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constructor_stem_size',
        verbose_name=_('Размер отверстия под шток'),
        help_text=_('Размер отверстия под шток арматуры')
    )
    actual_cable_glands_holes = models.ForeignKey(
        'electric_actuators.CableGlandHolesSet',
        related_name='constructor_cable_glands_holes',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Отверстия под кабельные вводы'),
        help_text=_('Отверстия под кабельные вводы')
    )

    # --- Выбранные опции: прямые FK на реальные опции ---
    # through_attr=None → through-модель САМА опция (FK на неё)
    # through_attr задан → FK на реальную опцию (params.xxx)

    selected_power_supply = models.ForeignKey(
        'electric_actuators.ElectricPowerSupplyOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Напряжение питания"),
        help_text=_('Выбранное напряжение питания')
    )

    selected_safety_position = models.ForeignKey(
        'params.SafetyPositionOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Положение безопасности"),
        help_text=_('Выбранное положение безопасности привода')
    )

    selected_control_unit_option = models.ForeignKey(
        'params.ControlUnitInstalledOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Блок управления"),
        help_text=_("Выбранный блок управления")
    )

    selected_temperature = models.ForeignKey(
        'electric_actuators.ElectricTemperatureOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Температурная опция"),
        help_text=_('Выбранная температурная опция')
    )

    # t° поля — синхронизируются с selected_temperature в save()
    work_temp_min = models.IntegerField(
        default=0,
        verbose_name=_('Т мин, °С'),
        help_text=_('Минимальная рабочая температура, °С')
    )
    work_temp_max = models.IntegerField(
        default=0,
        verbose_name=_('Т макс, °С'),
        help_text=_('Максимальная рабочая температура, °С')
    )

    selected_ip = models.ForeignKey(
        'params.IpOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Степень защиты IP"),
        help_text=_('Выбранная степень защиты IP')
    )

    selected_exd = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Взрывозащита"),
        help_text=_('Выбранная опция взрывозащиты')
    )

    selected_body_coating = models.ForeignKey(
        'params.BodyCoatingOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Покрытие корпуса"),
        help_text=_('Выбранное покрытие корпуса')
    )

    selected_body_color_option = models.ForeignKey(
        'params.BodyColor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Цвет"),
        help_text=_("Цвет корпуса")
    )

    selected_hand_wheel = models.ForeignKey(
        'params.HandWheelInstalledOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Встроенный дублер"),
        help_text=_('Встроенный ручной дублер')
    )

    selected_turn_angle_option = models.ForeignKey(
        'electric_actuators.ElectricTurnAngleOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Угол поворота"),
        help_text=_('Угол поворота')
    )

    selected_blinker_option = models.ForeignKey(
        'params.BlinkerOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Блинкер"),
        help_text=_("Тип установленного блинкера")
    )

    selected_mechanical_indicator_option = models.ForeignKey(
        'params.MechanicalIndicatorInstalledOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Механический индикатор"),
        help_text=_("Выбранный механический индикатор")
    )

    selected_cable_glands_holes = models.ForeignKey(
        'electric_actuators.CableGlandHolesSet',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='constructor_cg_option',
        verbose_name=_("Кабельные вводы"),
        help_text=_('Отверстия под кабельные вводы')
    )

    selected_end_switches_option = models.ForeignKey(
        'params.SwitchesParameters',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='constructor_end_switches',
        verbose_name=_("Конечные выключатели"),
        help_text=_("Конечные выключатели")
    )

    selected_way_switches_option = models.ForeignKey(
        'params.SwitchesParameters',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='constructor_way_switches',
        verbose_name=_("Путевые выключатели"),
        help_text=_("Путевые выключатели")
    )

    selected_torque_switches_option = models.ForeignKey(
        'params.SwitchesParameters',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='constructor_torque_switches',
        verbose_name=_("Моментные выключатели"),
        help_text=_("Моментные выключатели")
    )

    is_unique = models.BooleanField(default=True, verbose_name='Это уникальная конфигурация')

    # ==================== КОНФИГУРАЦИЯ ОПЦИЙ ====================
    # through_model_path — путь к through-модели для проверки доступности
    # through_attr — имя атрибута through-модели, указывающего на реальную опцию (None = through-модель сама опция)
    # parent_field — поле through-модели для фильтрации доступности
    # parent_resolver — опционально: имя поля конструктора для разрешения родителя (для safety_position/control_unit)
    _OPTION_CONFIG = {
        'selected_power_supply': {
            'through_model_path': 'electric_actuators.models.ea_model_line_item_options.ElectricPowerSupplyOption',
            'through_attr': None,  # ElectricPowerSupplyOption САМА является опцией
            'label': 'напряжение питания',
            'parent_field': 'model_line_item',
        },
        'selected_safety_position': {
            'through_model_path': 'electric_actuators.models.ea_model_line_item_options.ElectricSafetyPositionOption',
            'through_attr': 'safety_position',
            'label': 'положение безопасности',
            'parent_field': 'power_supply_option',
            'parent_resolver': 'selected_power_supply',
        },
        'selected_control_unit_option': {
            'through_model_path': 'electric_actuators.models.ea_model_line_item_options.ElectricControlUnitOption',
            'through_attr': 'control_unit',
            'label': 'блок управления',
            'parent_field': 'power_supply_option',
            'parent_resolver': 'selected_power_supply',
        },
        'selected_temperature': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricTemperatureOption',
            'through_attr': None,  # ElectricTemperatureOption САМА является опцией
            'label': 'температурная опция',
            'parent_field': 'model_line',
        },
        'selected_ip': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricIpOption',
            'through_attr': 'ip_option',
            'label': 'степень защиты IP',
            'parent_field': 'model_line',
        },
        'selected_exd': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricExdOption',
            'through_attr': 'exd_option',
            'label': 'взрывозащита',
            'parent_field': 'model_line',
        },
        'selected_body_coating': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricBodyCoatingOption',
            'through_attr': 'body_coating_option',
            'label': 'покрытие корпуса',
            'parent_field': 'model_line',
        },
        'selected_body_color_option': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricBodyColorOption',
            'through_attr': 'color_option',
            'label': 'цвет корпуса',
            'parent_field': 'model_line',
        },
        'selected_hand_wheel': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricHandWheelOption',
            'through_attr': 'hand_wheel_option',
            'label': 'ручной дублер',
            'parent_field': 'model_line',
        },
        'selected_turn_angle_option': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricTurnAngleOption',
            'through_attr': None,  # ElectricTurnAngleOption САМА является опцией
            'label': 'угол поворота',
            'parent_field': 'model_line',
        },
        'selected_blinker_option': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricBlinkerOption',
            'through_attr': 'blinker_option',
            'label': 'блинкер',
            'parent_field': 'model_line',
        },
        'selected_mechanical_indicator_option': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricMechanicalIndicatorOption',
            'through_attr': 'mechanical_indicator_option',
            'label': 'механический индикатор',
            'parent_field': 'model_line',
        },
        'selected_cable_glands_holes': {
            'through_model_path': 'electric_actuators.models.ea_options.CableGlandHolesSetBodyOption',
            'through_attr': 'cg_set',
            'label': 'кабельные вводы',
            'parent_field': 'model_body',
        },
        'selected_end_switches_option': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricEndSwitchesOption',
            'through_attr': 'end_switches_option',
            'label': 'концевые выключатели',
            'parent_field': 'model_line_item',
        },
        'selected_way_switches_option': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricWaySwitchesOption',
            'through_attr': 'way_switches_option',
            'label': 'путевые выключатели',
            'parent_field': 'model_line_item',
        },
        'selected_torque_switches_option': {
            'through_model_path': 'electric_actuators.models.ea_options.ElectricTorqueSwitchesOption',
            'through_attr': 'torque_switches_option',
            'label': 'моментные выключатели',
            'parent_field': 'model_line_item',
        },
    }

    @classmethod
    def get_option_fields(cls):
        """Возвращает список всех полей опций"""
        return list(cls._OPTION_CONFIG.keys())

    @classmethod
    def _import_through_model(cls, config: dict):
        """Импортирует through-модель по пути из конфига"""
        module_name, class_name = config['through_model_path'].rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    @classmethod
    def _get_actual_option_from_through(cls, through_instance, config: dict):
        """
        Извлекает реальную опцию из through-модели.
        Если through_attr is None — through-модель сама является опцией.
        """
        through_attr = config.get('through_attr')
        if through_attr is None:
            return through_instance
        return getattr(through_instance, through_attr, None)

    @classmethod
    def get_for_select(cls, model_line_id: Optional[int] = None,
                       model_line_item_id: Optional[int] = None,
                       active_only: bool = True) -> List[Dict]:
        """Получить список сконструированных приводов для выпадающего списка."""
        queryset = cls.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        if model_line_id:
            queryset = queryset.filter(selected_model_line_id=model_line_id)
        if model_line_item_id:
            queryset = queryset.filter(selected_model_line_item_id=model_line_item_id)
        return [{'id': obj.id, 'name': obj.name, 'code': obj.code} for obj in queryset]

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Конструктор электропривода')
        verbose_name_plural = _('Конструктор электроприводов')

    def __str__(self):
        return self.name

    # ==================== DISPLAY PROPERTIES ====================

    @property
    def selected_model_display(self):
        return str(self.selected_model_line_item) if self.selected_model_line_item else "-"

    @property
    def safety_position_display(self):
        return str(self.selected_safety_position) if self.selected_safety_position else "-"

    @property
    def power_supply_display(self):
        return str(self.selected_power_supply) if self.selected_power_supply else "-"

    @property
    def temperature_display(self):
        return str(self.selected_temperature) if self.selected_temperature else "-"

    @property
    def ip_display(self):
        return str(self.selected_ip) if self.selected_ip else "-"

    @property
    def exd_display(self):
        return str(self.selected_exd) if self.selected_exd else "-"

    @property
    def body_coating_display(self):
        return str(self.selected_body_coating) if self.selected_body_coating else "-"

    @property
    def hand_wheel_display(self):
        return str(self.selected_hand_wheel) if self.selected_hand_wheel else "-"

    @property
    def description_preview(self):
        """Превью описания для админки."""
        return self.description[:200] + '...' if self.description and len(self.description) > 200 else (self.description or '')

    # ==================== GET AVAILABLE OPTIONS ====================

    def _get_parent_for_option(self, config: dict):
        """
        Возвращает родительский объект для фильтрации через through-модель.
        Для обычных опций: model_line, model_line_item, model_body.
        Для опций с parent_resolver: берёт значение из поля конструктора.
        """
        resolver = config.get('parent_resolver')
        if resolver:
            return getattr(self, resolver, None)

        parent_field = config.get('parent_field')
        if parent_field == 'model_line':
            if self.selected_model_line_item:
                return self.selected_model_line_item.model_line
            return self.selected_model_line
        elif parent_field == 'model_line_item':
            return self.selected_model_line_item
        elif parent_field == 'model_body':
            if self.selected_model_line_item:
                return self.selected_model_line_item.body
            return None
        return None

    def get_available_options(self) -> Dict[str, List[Dict]]:
        """
        Получить все доступные опции для выбранной модели.
        Возвращает словарь: ключ — имя поля опции, значение — список {id, option_id, name, code, is_default, ...}.
        option_id — это ID реальной опции (для подстановки в FK Конструктора).
        Для through_attr=None: id и option_id совпадают (through-модель сама опция).
        """
        if not self.selected_model_line_item:
            return {}

        result = {}

        # --- model_line_item опции ---
        if self.selected_model_line_item:
            mli = self.selected_model_line_item

            # power_supply (through_attr=None)
            ps_config = self._OPTION_CONFIG['selected_power_supply']
            PowerSupplyModel = self._import_through_model(ps_config)
            ps_through = PowerSupplyModel.objects.filter(
                model_line_item=mli, is_active=True
            ).select_related('power_supply')
            result['power_supply_options'] = [
                {
                    'id': opt.id, 'option_id': opt.id,
                    'encoding': opt.power_supply.encoding or opt.encoding,
                    'name': str(opt.power_supply),
                    'description': opt.power_supply.description or opt.description or '',
                    'is_default': False,
                    'power_supply_id': opt.power_supply_id,
                }
                for opt in ps_through
            ]

        # Опции через model_line
        ml = self.selected_model_line_item.model_line if self.selected_model_line_item else None
        if ml:
            for field_name in ['selected_temperature', 'selected_ip', 'selected_exd',
                               'selected_body_coating', 'selected_body_color_option',
                               'selected_hand_wheel', 'selected_turn_angle_option',
                               'selected_blinker_option', 'selected_mechanical_indicator_option']:
                config = self._OPTION_CONFIG[field_name]
                ThroughModel = self._import_through_model(config)
                through_attr = config.get('through_attr')
                filter_kwargs = {config['parent_field']: ml, 'is_active': True}

                if through_attr is None:
                    # through-модель сама опция
                    qs = ThroughModel.objects.filter(**filter_kwargs)
                    if field_name in ('selected_temperature', 'selected_ip', 'selected_exd'):
                        qs = qs.order_by('is_default', 'sorting_order')
                    key = field_name.replace('selected_', '') + '_options'
                    if key.endswith('_option_options'):
                        key = key.replace('_option_options', '_options')
                    result[key] = [
                        {
                            'id': opt.id, 'option_id': opt.id,
                            'encoding': opt.encoding or '',
                            'name': str(opt),
                            'description': opt.description or '',
                            'is_default': opt.is_default,
                        }
                        for opt in qs
                    ]
                else:
                    # FK на реальную опцию
                    select_related = [through_attr]
                    qs = ThroughModel.objects.filter(**filter_kwargs).select_related(*select_related)
                    key = field_name.replace('selected_', '') + '_options'
                    if key.endswith('_option_options'):
                        key = key.replace('_option_options', '_options')
                    result[key] = [
                        {
                            'id': opt.id,
                            'option_id': getattr(opt, through_attr).id,
                            'encoding': opt.encoding or '',
                            'name': getattr(opt, through_attr).name,
                            'code': getattr(opt, through_attr, None) and getattr(getattr(opt, through_attr), 'code', ''),
                            'description': opt.description or '',
                            'is_default': opt.is_default,
                        }
                        for opt in qs
                    ]

        # --- model_line_item опции ---
        if self.selected_model_line_item:
            for field_name in ['selected_end_switches_option', 'selected_way_switches_option',
                               'selected_torque_switches_option']:
                config = self._OPTION_CONFIG[field_name]
                ThroughModel = self._import_through_model(config)
                through_attr = config.get('through_attr')
                filter_kwargs = {config['parent_field']: self.selected_model_line_item, 'is_active': True}
                qs = ThroughModel.objects.filter(**filter_kwargs).select_related(through_attr)
                key = field_name.replace('selected_', '') + '_options'
                if key.endswith('_option_options'):
                    key = key.replace('_option_options', '_options')
                result[key] = [
                    {
                        'id': opt.id,
                        'option_id': getattr(opt, through_attr).id,
                        'encoding': opt.encoding or '',
                        'name': getattr(opt, through_attr).name,
                        'code': getattr(opt, through_attr).code if hasattr(getattr(opt, through_attr), 'code') else '',
                        'description': opt.description or '',
                        'is_default': opt.is_default,
                    }
                    for opt in qs
                ]

        # --- model_body опции ---
        body = self.selected_model_line_item.body if self.selected_model_line_item else None
        if body:
            field_name = 'selected_cable_glands_holes'
            config = self._OPTION_CONFIG[field_name]
            ThroughModel = self._import_through_model(config)
            through_attr = config.get('through_attr')
            qs = ThroughModel.objects.filter(**{config['parent_field']: body}, is_active=True).select_related(through_attr)
            key = field_name.replace('selected_', '') + '_options'
            result[key] = [
                {
                    'id': opt.id,
                    'option_id': getattr(opt, through_attr).id,
                    'encoding': opt.encoding or '',
                    'name': getattr(opt, through_attr).name,
                    'code': getattr(opt, through_attr).code if hasattr(getattr(opt, through_attr), 'code') else '',
                    'description': opt.description or '',
                    'is_default': opt.is_default,
                }
                for opt in qs
            ]

        # --- power_supply-зависимые опции (safety_position, control_unit) ---
        if self.selected_power_supply:
            for field_name in ['selected_safety_position', 'selected_control_unit_option']:
                config = self._OPTION_CONFIG[field_name]
                ThroughModel = self._import_through_model(config)
                through_attr = config.get('through_attr')
                filter_kwargs = {config['parent_field']: self.selected_power_supply, 'is_active': True}
                qs = ThroughModel.objects.filter(**filter_kwargs).select_related(through_attr)
                key = field_name.replace('selected_', '') + '_options'
                if key.endswith('_option_options'):
                    key = key.replace('_option_options', '_options')
                result[key] = [
                    {
                        'id': opt.id,
                        'option_id': getattr(opt, through_attr).id,
                        'encoding': opt.encoding or '',
                        'name': getattr(opt, through_attr).name,
                        'code': getattr(opt, through_attr).code if hasattr(getattr(opt, through_attr), 'code') else '',
                        'description': opt.description or '',
                        'is_default': opt.is_default,
                    }
                    for opt in qs
                ]

        return result

    # ==================== ВАЛИДАЦИЯ ОПЦИЙ ====================

    def _ensure_valid_options(self):
        """
        Гарантирует, что все опции валидны для текущей модели.
        Для полей с through_attr: запрашивает through-модель, извлекает реальную опцию.
        Для полей без through_attr: through-модель сама опция.
        """
        if not self.selected_model_line_item:
            return

        for field_name, config in self._OPTION_CONFIG.items():
            if not getattr(self, field_name):
                self._set_default_option(field_name, config)

        for field_name, config in self._OPTION_CONFIG.items():
            current_value = getattr(self, field_name)
            if current_value:
                self._validate_option(field_name, current_value, config)

    def _set_default_option(self, field_name, config):
        """
        Установить дефолтную опцию для незаполненного поля.
        Запрашивает through-модель по родителю, ищет is_default=True.
        Если не найдено — берёт первую активную.
        """
        ThroughModel = self._import_through_model(config)
        parent_obj = self._get_parent_for_option(config)
        if not parent_obj:
            return

        # Пропускаем power_supply-зависимые опции если нет selected_power_supply
        resolver = config.get('parent_resolver')
        if resolver and not getattr(self, resolver, None):
            return

        filter_kwargs = {config['parent_field']: parent_obj, 'is_active': True}
        default_option = ThroughModel.objects.filter(is_default=True, **filter_kwargs).first()

        if not default_option:
            default_option = ThroughModel.objects.filter(**filter_kwargs).first()

        if default_option:
            actual_option = self._get_actual_option_from_through(default_option, config)
            setattr(self, field_name, actual_option)

    def _validate_option(self, field_name, current_value, config):
        """
        Проверяет, что выбранная опция доступна через through-модель.
        Если нет — заменяет на дефолтную/первую доступную.
        """
        ThroughModel = self._import_through_model(config)
        parent_obj = self._get_parent_for_option(config)
        if not parent_obj:
            return

        resolver = config.get('parent_resolver')
        if resolver and not getattr(self, resolver, None):
            return

        filter_kwargs = {config['parent_field']: parent_obj, 'is_active': True}
        through_attr = config.get('through_attr')

        if through_attr is None:
            # through-модель сама опция
            valid = ThroughModel.objects.filter(id=current_value.id, **filter_kwargs).exists()
        else:
            # Фильтруем по ID реальной опции
            valid = ThroughModel.objects.filter(**{f'{through_attr}_id': current_value.id}, **filter_kwargs).exists()

        if not valid:
            logger.warning(
                f'Выбранная {config["label"]} не доступна для модели {self.selected_model_line_item}. '
                f'Заменяется на дефолтную.'
            )
            # Сбрасываем и ставим дефолт
            setattr(self, field_name, None)
            self._set_default_option(field_name, config)

    def clean(self):
        """Мягкая валидация выбранных опций через through-модели"""
        if not self.selected_model_line_item:
            return

        for field_name, config in self._OPTION_CONFIG.items():
            field_value = getattr(self, field_name)
            if field_value:
                try:
                    ThroughModel = self._import_through_model(config)
                    parent_obj = self._get_parent_for_option(config)
                    if not parent_obj:
                        continue

                    resolver = config.get('parent_resolver')
                    if resolver and not getattr(self, resolver, None):
                        continue

                    filter_kwargs = {'is_active': True}
                    filter_kwargs[config['parent_field']] = parent_obj

                    through_attr = config.get('through_attr')
                    if through_attr is None:
                        filter_kwargs['id'] = field_value.id
                    else:
                        filter_kwargs[f'{through_attr}_id'] = field_value.id

                    valid_option = ThroughModel.objects.filter(**filter_kwargs).exists()

                    if not valid_option:
                        logger.warning(
                            f'Выбранная {config["label"]} не доступна для модели {self.selected_model_line_item}.'
                        )
                except Exception as e:
                    logger.error(f"Error validating {field_name}: {e}")

    # ==================== ГЕНЕРАЦИЯ КОДА ====================

    def _get_option_encoding(self, field_name: str) -> str:
        """
        Возвращает encoding опции из through-модели (не code реальной опции!).
        Для code-генерации важно брать encoding — он задаётся в through-моделях
        и соответствует шаблону артикула.
        """
        config = self._OPTION_CONFIG.get(field_name)
        if not config:
            return ''
        option_value = getattr(self, field_name)
        if not option_value:
            return ''

        through_attr = config.get('through_attr')
        if through_attr is None:
            # Temperature / PowerSupply / TurnAngle: through-модель САМА опция
            return getattr(option_value, 'encoding', '') or ''

        # Остальные: ищем through-запись по ID реальной опции + родителю
        ThroughModel = self._import_through_model(config)
        parent_obj = self._get_parent_for_option(config)
        if not parent_obj:
            return ''

        resolver = config.get('parent_resolver')
        if resolver and not getattr(self, resolver, None):
            return ''

        through_instance = ThroughModel.objects.filter(
            **{f'{through_attr}_id': option_value.id, config['parent_field']: parent_obj}
        ).first()
        return through_instance.encoding if through_instance and through_instance.encoding else ''

    def _get_value_old(self, field_path: str) -> str:
        """
        Обход цепочки атрибутов через двойное подчёркивание.
        Например, 'selected_model_line_item__code' → self.selected_model_line_item.code.
        Возвращает пустую строку если любой элемент цепочки — None.
        """
        try:
            current_obj = self
            for field_name in field_path.split('__'):
                current_obj = getattr(current_obj, field_name, None)
                if current_obj is None:
                    return ""
            return str(current_obj) if current_obj else ""
        except Exception:
            return ""

    @property
    def generated_model_item_code(self) -> str:
        """
        Генерирует артикул (code) по шаблону model_line.model_item_code_template.
        Поддерживает переменные: {model_code}, {rotation_speed}, {temperature},
        {ip}, {voltage}, {exd}, {control_unit}.
        Если шаблон отсутствует — вызывает _generate_fallback_code().
        """
        if not self.selected_model_line_item or not self.selected_model_line_item.model_line:
            return self.code or ""

        template = self.selected_model_line_item.model_line.model_item_code_template
        if not template:
            return self._generate_fallback_code()

        result = template
        result = result.replace('{model_code}', self._get_value_old('selected_model_line_item__name'))
        result = result.replace('{rotation_speed}', self._get_value_old('selected_model_line_item__rotation_speed'))
        result = result.replace('{temperature}', self._get_option_encoding('selected_temperature'))
        result = result.replace('{ip}', self._get_option_encoding('selected_ip'))
        result = result.replace('{voltage}', self._get_option_encoding('selected_power_supply'))
        result = result.replace('{exd}', self._get_option_encoding('selected_exd'))
        result = result.replace('{control_unit}', self._get_option_encoding('selected_control_unit_option'))

        # Очистка
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\.\s+', ' ', result)
        result = result.strip('.')

        return result

    def _generate_fallback_code(self) -> str:
        """Простая резервная генерация кода"""
        parts = [
            self._get_value_old('selected_model_line_item__code'),
            self._get_option_encoding('selected_power_supply'),
            self._get_option_encoding('selected_temperature'),
            self._get_option_encoding('selected_control_unit_option'),
            self._get_option_encoding('selected_ip'),
            self._get_option_encoding('selected_exd'),
        ]
        return '.'.join(filter(None, parts))

    # ==================== ГЕНЕРАЦИЯ ОПИСАНИЙ ====================

    def get_description_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Унифицированная плоская структура данных для описания.
        Использует прямые FK (не through-модели).
        """
        data = {}

        # --- MODEL INFO ---
        item = self.selected_model_line_item
        data['model_name'] = {
            'category': 'model',
            'title': 'Модель',
            'data': item.id if item else None,
            'display_data': str(item) if item else 'Не указано',
            'code': item.code if item else '',
            'name': str(item) if item else '',
        }
        data['model_line_name'] = {
            'category': 'model',
            'title': 'Серия',
            'data': item.model_line.id if item and item.model_line else None,
            'display_data': str(item.model_line) if item and item.model_line else 'Не указано',
            'code': item.model_line.code if item and item.model_line else '',
            'name': str(item.model_line) if item and item.model_line else '',
        }

        # --- CONSTRUCTION FEATURES ---
        data['rotation_speed'] = {
            'category': 'model',
            'title': 'Скорость вращения',
            'data': item.rotation_speed if item else None,
            'display_data': f"{item.rotation_speed} об/мин" if item and item.rotation_speed else 'Не указано',
        }
        data['torque_min'] = {
            'category': 'model',
            'title': 'Мин. момент',
            'data': item.torque_min if item else None,
            'display_data': f"{item.torque_min} Нм" if item and item.torque_min else 'Не указано',
        }
        data['torque_max'] = {
            'category': 'model',
            'title': 'Макс. момент',
            'data': item.torque_max if item else None,
            'display_data': f"{item.torque_max} Нм" if item and item.torque_max else 'Не указано',
        }
        data['time_to_open'] = {
            'category': 'model',
            'title': 'Время открытия',
            'data': item.time_to_open if item else None,
            'display_data': f"{item.time_to_open} сек" if item and item.time_to_open else 'Не указано',
        }
        data['time_to_close'] = {
            'category': 'model',
            'title': 'Время закрытия',
            'data': item.time_to_close if item else None,
            'display_data': f"{item.time_to_close} сек" if item and item.time_to_close else 'Не указано',
        }

        # --- SELECTED OPTIONS ---
        # power_supply → ElectricPowerSupplyOption (through_attr=None)
        ps = self.selected_power_supply
        data['power_supply'] = {
            'category': 'selected_options',
            'title': 'Напряжение питания',
            'data': ps.id if ps else None,
            'display_data': str(ps) if ps else 'Не указано',
            'code': ps.encoding if (ps and ps.encoding) else '',
            'name': str(ps) if ps else '',
        }
        if ps:
            data['motor_power'] = {
                'category': 'selected_options',
                'title': 'Мощность двигателя',
                'data': float(ps.motor_power) if ps.motor_power else None,
                'display_data': f"{ps.motor_power} кВт" if ps.motor_power else 'Не указано',
            }
            data['motor_current_rated'] = {
                'category': 'selected_options',
                'title': 'Ток номинальный',
                'data': float(ps.motor_current_rated) if ps.motor_current_rated else None,
                'display_data': f"{ps.motor_current_rated} А" if ps.motor_current_rated else 'Не указано',
            }
            data['motor_current_starting'] = {
                'category': 'selected_options',
                'title': 'Ток пусковой',
                'data': float(ps.motor_current_starting) if ps.motor_current_starting else None,
                'display_data': f"{ps.motor_current_starting} А" if ps.motor_current_starting else 'Не указано',
            }

        # safety_position → params.SafetyPositionOption
        sp = self.selected_safety_position
        data['safety_position'] = {
            'category': 'selected_options',
            'title': 'Положение безопасности',
            'data': sp.id if sp else None,
            'display_data': sp.name if sp else 'Не указано',
            'code': sp.code if sp else '',
            'name': sp.name if sp else '',
        }

        # control_unit → params.ControlUnitInstalledOption
        cu = self.selected_control_unit_option
        data['control_unit'] = {
            'category': 'selected_options',
            'title': 'Блок управления',
            'data': cu.id if cu else None,
            'display_data': cu.name if cu else 'Не указано',
            'code': cu.code if cu else '',
            'name': cu.name if cu else '',
        }

        # temperature → ElectricTemperatureOption (through_attr=None)
        st = self.selected_temperature
        data['temperature'] = {
            'category': 'selected_options',
            'title': 'Температурное исполнение',
            'data': st.id if st else None,
            'display_data': str(st) if st else 'Не указано',
            'code': st.encoding if (st and st.encoding) else '',
            'name': str(st) if st else '',
            'work_temp_min': st.work_temp_min if st else None,
            'work_temp_max': st.work_temp_max if st else None,
            'is_default': st.is_default if st else None,
        }

        # ip → params.IpOption
        ip = self.selected_ip
        data['ip'] = {
            'category': 'selected_options',
            'title': 'IP защита',
            'data': ip.id if ip else None,
            'display_data': ip.name if ip else 'Не указано',
            'code': ip.code if ip else '',
            'name': ip.name if ip else '',
        }

        # exd → params.ExdOption
        ex = self.selected_exd
        data['exd'] = {
            'category': 'selected_options',
            'title': 'Взрывозащита',
            'data': ex.id if ex else None,
            'display_data': ex.name if ex else 'Не указано',
            'code': ex.code if ex else '',
            'name': ex.name if ex else '',
        }

        # body_coating → params.BodyCoatingOption
        bc = self.selected_body_coating
        data['body_coating'] = {
            'category': 'selected_options',
            'title': 'Покрытие корпуса',
            'data': bc.id if bc else None,
            'display_data': bc.name if bc else 'Не указано',
            'code': bc.code if bc else '',
            'name': bc.name if bc else '',
        }

        # body_color → params.BodyColor
        bco = self.selected_body_color_option
        data['body_color'] = {
            'category': 'selected_options',
            'title': 'Цвет корпуса',
            'data': bco.id if bco else None,
            'display_data': bco.name if bco else 'Не указано',
            'code': bco.code if bco else '',
            'name': bco.name if bco else '',
        }

        # hand_wheel → params.HandWheelInstalledOption
        hw = self.selected_hand_wheel
        data['hand_wheel'] = {
            'category': 'selected_options',
            'title': 'Ручной дублер',
            'data': hw.id if hw else None,
            'display_data': hw.name if hw else 'Не указано',
            'code': hw.code if hw else '',
            'name': hw.name if hw else '',
        }

        # turn_angle → ElectricTurnAngleOption (through_attr=None)
        ta = self.selected_turn_angle_option
        data['turn_angle'] = {
            'category': 'selected_options',
            'title': 'Угол поворота',
            'data': ta.id if ta else None,
            'display_data': f"{ta.turn_angle}°" if ta and ta.turn_angle else 'Не указано',
            'code': ta.encoding if (ta and ta.encoding) else '',
            'name': str(ta) if ta else '',
            'turn_angle_value': ta.turn_angle if ta else None,
            'turn_angle_deviation_limit': ta.turn_angle_deviation_limit if ta else None,
        }

        # blinker → params.BlinkerOption
        bl = self.selected_blinker_option
        data['blinker'] = {
            'category': 'selected_options',
            'title': 'Блинкер',
            'data': bl.id if bl else None,
            'display_data': bl.name if bl else 'Не указано',
            'code': bl.code if bl else '',
            'name': bl.name if bl else '',
        }

        # mechanical_indicator → params.MechanicalIndicatorInstalledOption
        mi = self.selected_mechanical_indicator_option
        data['mechanical_indicator'] = {
            'category': 'selected_options',
            'title': 'Механический индикатор',
            'data': mi.id if mi else None,
            'display_data': mi.name if mi else 'Не указано',
            'code': mi.code if mi else '',
            'name': mi.name if mi else '',
        }

        # cable_glands_holes → CableGlandHolesSet
        cg = self.selected_cable_glands_holes
        data['cable_glands_holes'] = {
            'category': 'selected_options',
            'title': 'Кабельные вводы',
            'data': cg.id if cg else None,
            'display_data': str(cg) if cg else 'Не указано',
        }

        # end_switches → params.SwitchesParameters
        es = self.selected_end_switches_option
        data['end_switches'] = {
            'category': 'selected_options',
            'title': 'Концевые выключатели',
            'data': es.id if es else None,
            'display_data': es.name if es else 'Не указано',
            'code': es.code if es else '',
            'name': es.name if es else '',
        }

        # way_switches → params.SwitchesParameters
        ws = self.selected_way_switches_option
        data['way_switches'] = {
            'category': 'selected_options',
            'title': 'Путевые выключатели',
            'data': ws.id if ws else None,
            'display_data': ws.name if ws else 'Не указано',
            'code': ws.code if ws else '',
            'name': ws.name if ws else '',
        }

        # torque_switches → params.SwitchesParameters
        ts = self.selected_torque_switches_option
        data['torque_switches'] = {
            'category': 'selected_options',
            'title': 'Моментные выключатели',
            'data': ts.id if ts else None,
            'display_data': ts.name if ts else 'Не указано',
            'code': ts.code if ts else '',
            'name': ts.name if ts else '',
        }

        # --- MOUNTING ---
        data['mounting_plate'] = {
            'category': 'construction',
            'title': 'Монтажная площадка',
            'data': self.actual_mounting_plate.id if self.actual_mounting_plate else None,
            'display_data': self.actual_mounting_plate.name if self.actual_mounting_plate else 'Не указано',
        }
        data['stem_shape'] = {
            'category': 'construction',
            'title': 'Тип отверстия под шток',
            'data': self.actual_stem_shape.id if self.actual_stem_shape else None,
            'display_data': str(self.actual_stem_shape.name) if self.actual_stem_shape else 'Не указано',
        }
        data['stem_size'] = {
            'category': 'construction',
            'title': 'Размер отверстия под шток',
            'data': self.actual_stem_size.id if self.actual_stem_size else None,
            'display_data': self.actual_stem_size.name if self.actual_stem_size else 'Не указано',
        }

        # --- ACTUAL CABLE GLANDS (construction) ---
        acg = self.actual_cable_glands_holes
        data['actual_cable_glands_holes'] = {
            'category': 'construction',
            'title': 'Отверстия под КВ (факт)',
            'data': acg.id if acg else None,
            'display_data': str(acg) if acg else 'Не указано',
        }

        return data

    def _generate_short_description(self) -> str:
        """Генерация краткого текстового описания привода."""
        data = self.get_description_data()
        desc_parts = []

        # Заголовок
        model_name = data.get('model_name', {}).get('display_data')
        model_line_name = data.get('model_line_name', {}).get('display_data')
        if model_line_name and model_line_name != 'Не указано':
            desc_parts.append(f"Электропривод {model_name} (серия {model_line_name})")
        else:
            desc_parts.append(f"Электропривод {model_name}" if model_name else "Электропривод")

        # Основные характеристики модели
        specs = []
        rotation_speed = data.get('rotation_speed', {}).get('display_data')
        if rotation_speed and rotation_speed != 'Не указано':
            specs.append(rotation_speed)
        torque_min = data.get('torque_min', {}).get('display_data')
        torque_max = data.get('torque_max', {}).get('display_data')
        if torque_min and torque_max and torque_min != 'Не указано' and torque_max != 'Не указано':
            specs.append(f"Момент: {torque_min} / {torque_max}")
        tto = data.get('time_to_open', {}).get('display_data')
        ttc = data.get('time_to_close', {}).get('display_data')
        if tto and ttc and tto != 'Не указано' and ttc != 'Не указано':
            specs.append(f"Время: {tto} / {ttc}")
        motor_power = data.get('motor_power', {}).get('display_data')
        if motor_power and motor_power != 'Не указано':
            specs.append(motor_power)
        motor_rated = data.get('motor_current_rated', {}).get('display_data')
        if motor_rated and motor_rated != 'Не указано':
            specs.append(motor_rated)
        motor_start = data.get('motor_current_starting', {}).get('display_data')
        if motor_start and motor_start != 'Не указано':
            specs.append(f"Iпуск={motor_start}")
        if specs:
            desc_parts.append("Характеристики: " + ", ".join(specs))

        # Выбранные опции
        selected_options = []
        for key in ['power_supply', 'safety_position', 'control_unit', 'temperature',
                     'ip', 'exd', 'body_coating', 'body_color', 'hand_wheel',
                     'turn_angle', 'blinker', 'mechanical_indicator',
                     'cable_glands_holes', 'end_switches', 'way_switches', 'torque_switches']:
            opt = data.get(key, {})
            display = opt.get('display_data')
            if display and display != 'Не указано':
                title = opt.get('title', key)
                selected_options.append(f"{title}: {display}")

        if selected_options:
            desc_parts.append("Выбранные опции: " + "; ".join(selected_options))

        # Присоединение
        mount = []
        mp = data.get('mounting_plate', {}).get('display_data')
        if mp and mp != 'Не указано':
            mount.append(f"монтажная площадка: {mp}")
        ss = data.get('stem_shape', {}).get('display_data')
        if ss and ss != 'Не указано':
            mount.append(f"шток: {ss}")
        sz = data.get('stem_size', {}).get('display_data')
        if sz and sz != 'Не указано':
            mount.append(f"размер: {sz}")
        if mount:
            desc_parts.append("Присоединение: " + ", ".join(mount))

        return "\n".join(desc_parts)

    def _generate_tech_description(self) -> str:
        """
        Полное техническое описание.
        Возвращает текст с HTML-таблицей характеристик.
        """
        data = self.get_description_data()
        desc_parts = []

        # Заголовок
        model_name = data.get('model_name', {}).get('display_data')
        model_line = data.get('model_line_name', {}).get('display_data')
        desc_parts.append(f'<h3>Электропривод {model_name}</h3>')
        if model_line and model_line != 'Не указано':
            desc_parts.append(f'<p>Серия: {model_line}</p>')

        # Таблица характеристик
        desc_parts.append('<table border="1" style="border-collapse: collapse; margin: 4px 0; width: 100%;">')
        desc_parts.append('<tr><th>Параметр</th><th>Значение</th></tr>')

        rows = [
            ('Скорость вращения', data.get('rotation_speed', {})),
            ('Мин. момент', data.get('torque_min', {})),
            ('Макс. момент', data.get('torque_max', {})),
            ('Время открытия', data.get('time_to_open', {})),
            ('Время закрытия', data.get('time_to_close', {})),
            ('Напряжение питания', data.get('power_supply', {})),
            ('Мощность двигателя', data.get('motor_power', {})),
            ('Ток номинальный', data.get('motor_current_rated', {})),
            ('Ток пусковой', data.get('motor_current_starting', {})),
            ('Положение безопасности', data.get('safety_position', {})),
            ('Блок управления', data.get('control_unit', {})),
            ('Температурное исполнение', data.get('temperature', {})),
            ('IP защита', data.get('ip', {})),
            ('Взрывозащита', data.get('exd', {})),
            ('Покрытие корпуса', data.get('body_coating', {})),
            ('Цвет корпуса', data.get('body_color', {})),
            ('Ручной дублер', data.get('hand_wheel', {})),
            ('Угол поворота', data.get('turn_angle', {})),
            ('Блинкер', data.get('blinker', {})),
            ('Механический индикатор', data.get('mechanical_indicator', {})),
            ('Кабельные вводы', data.get('cable_glands_holes', {})),
            ('Концевые выключатели', data.get('end_switches', {})),
            ('Путевые выключатели', data.get('way_switches', {})),
            ('Моментные выключатели', data.get('torque_switches', {})),
            ('Монтажная площадка', data.get('mounting_plate', {})),
            ('Тип отверстия под шток', data.get('stem_shape', {})),
            ('Размер отверстия под шток', data.get('stem_size', {})),
        ]
        for label, opt in rows:
            display = opt.get('display_data') if opt else None
            if display and display != 'Не указано':
                desc_parts.append(f'<tr><td>{label}</td><td>{display}</td></tr>')

        desc_parts.append('</table>')
        return '\n'.join(desc_parts)

    def _generate_html_description(self) -> str:
        """Генерация HTML-описания для rich-отображения."""
        return self._generate_tech_description()

    def get_structured_data(self) -> Dict[str, Any]:
        """
        Структурированные данные для API-ответа.
        """
        data = self.get_description_data()
        structured = {
            'model': {
                'name': data.get('model_name', {}).get('display_data'),
                'code': self.code,
            },
            'selected_options': {
                'power_supply': data.get('power_supply', {}).get('display_data'),
                'safety_position': data.get('safety_position', {}).get('display_data'),
                'control_unit': data.get('control_unit', {}).get('display_data'),
                'temperature': data.get('temperature', {}).get('display_data'),
                'ip': data.get('ip', {}).get('display_data'),
                'exd': data.get('exd', {}).get('display_data'),
                'body_coating': data.get('body_coating', {}).get('display_data'),
                'body_color': data.get('body_color', {}).get('display_data'),
                'hand_wheel': data.get('hand_wheel', {}).get('display_data'),
                'turn_angle': data.get('turn_angle', {}).get('display_data'),
                'blinker': data.get('blinker', {}).get('display_data'),
                'mechanical_indicator': data.get('mechanical_indicator', {}).get('display_data'),
                'cable_glands_holes': data.get('cable_glands_holes', {}).get('display_data'),
                'end_switches': data.get('end_switches', {}).get('display_data'),
                'way_switches': data.get('way_switches', {}).get('display_data'),
                'torque_switches': data.get('torque_switches', {}).get('display_data'),
            },
            'formatted': {
                'short': self._generate_short_description(),
                'technical': self._generate_tech_description(),
                'html': self._generate_html_description(),
            }
        }
        return structured

    # ==================== ДУБЛИКАТЫ ====================

    def _check_for_duplicates(self):
        """Проверка на дубликаты в базе данных"""
        filters = {}
        if self.selected_model_line_item:
            filters['selected_model_line_item'] = self.selected_model_line_item
        else:
            filters['selected_model_line_item__isnull'] = True

        for field_name in self.get_option_fields():
            field_value = getattr(self, field_name)
            if field_value:
                filters[field_name] = field_value
            else:
                filters[f'{field_name}__isnull'] = True

        if self.selected_model_line:
            filters['selected_model_line'] = self.selected_model_line
        else:
            filters['selected_model_line__isnull'] = True

        if filters:
            duplicates = self.__class__.objects.filter(**filters)
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)
            if duplicates.exists():
                duplicate = duplicates.first()
                return f"Найдена похожая конфигурация: {duplicate} (ID: {duplicate.id})"
        return None

    def _adjust_for_duplicate(self):
        """
        Добавляет суффикс (copy#XX) к name и code при обнаружении дубликата.
        """
        if not self.name:
            return

        from django.db.models import Q

        base_name_for_search = re.sub(r'\s*\(copy\s*#\d+\)$', '', self.name, flags=re.IGNORECASE).strip()

        existing_copies = self.__class__.objects.filter(
            Q(name=self.name) |
            Q(name__iregex=r'^' + re.escape(base_name_for_search) + r'\s*\(copy\s*#\d+\)$')
        )

        max_number = 0
        for copy in existing_copies:
            match = re.search(r'\(copy\s*#(\d+)\)$', copy.name, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                max_number = max(max_number, num)
            elif copy.name == self.name:
                max_number = max(max_number, 1)

        new_number = max_number + 1
        formatted_number = f"{new_number:02d}"
        self.name = f"{self.name} (copy#{formatted_number})"

        if self.code:
            clean_code = re.sub(r'\s*\(copy\s*#\d+\)$', '', self.code, flags=re.IGNORECASE)
            self.code = f"{clean_code} (copy#{formatted_number})"

    # ==================== SAVE ====================

    def save(self, *args, **kwargs):
        """
        Сохраняет конструктор с полным lifecycle:
        1. Валидация и автозаполнение опций через through-модели.
        2. Синхронизация work_temp_min/max из выбранной температуры.
        3. Автогенерация name, code, description.
        4. Проверка на дубликат — при совпадении добавляет суффикс (copy#XX).
        """
        self._ensure_valid_options()

        if self.selected_temperature:
            self.work_temp_min = self.selected_temperature.work_temp_min
            self.work_temp_max = self.selected_temperature.work_temp_max

        self.name = self.generated_model_item_code
        self.code = self.generated_model_item_code
        self.description = self._generate_short_description()

        duplicate_message = self._check_for_duplicates()
        if duplicate_message:
            self.is_unique = False
            self._adjust_for_duplicate()
            logger.warning(f"Создается дубликат: {duplicate_message}")
        else:
            self.is_unique = True

        super().save(*args, **kwargs)

    # ==================== ДУБЛИРОВАНИЕ ====================

    def create_duplicate(self):
        """
        Создать полную копию текущей конфигурации.
        Копирует все FK опций, генерирует новый name/code через save(),
        затем добавляет суффикс (copy#XX) через _adjust_for_duplicate().
        """
        duplicate = self.__class__(
            selected_model_line=self.selected_model_line,
            selected_model_line_item=self.selected_model_line_item,
            selected_power_supply=self.selected_power_supply,
            selected_safety_position=self.selected_safety_position,
            selected_control_unit_option=self.selected_control_unit_option,
            selected_temperature=self.selected_temperature,
            selected_ip=self.selected_ip,
            selected_exd=self.selected_exd,
            selected_body_coating=self.selected_body_coating,
            selected_body_color_option=self.selected_body_color_option,
            selected_hand_wheel=self.selected_hand_wheel,
            selected_turn_angle_option=self.selected_turn_angle_option,
            selected_blinker_option=self.selected_blinker_option,
            selected_mechanical_indicator_option=self.selected_mechanical_indicator_option,
            selected_cable_glands_holes=self.selected_cable_glands_holes,
            selected_end_switches_option=self.selected_end_switches_option,
            selected_way_switches_option=self.selected_way_switches_option,
            selected_torque_switches_option=self.selected_torque_switches_option,
            actual_mounting_plate=self.actual_mounting_plate,
            actual_stem_shape=self.actual_stem_shape,
            actual_stem_size=self.actual_stem_size,
            actual_cable_glands_holes=self.actual_cable_glands_holes,
            sorting_order=self.sorting_order,
            is_active=self.is_active,
            is_unique=False,
            name='',
            code='',
            description=self.description,
        )

        duplicate.save()

        if duplicate.name:
            duplicate._adjust_for_duplicate()
            duplicate.save()

        return duplicate
