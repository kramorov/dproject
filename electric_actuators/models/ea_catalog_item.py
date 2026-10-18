# electric_actuators/models/ea_catalog_item.py
"""
Эталонная каталожная карточка электропривода — ElectricActuatorCatalogItem.

Работает по единому контракту каталога (template_mixin.md, образец —
PneumaticActuatorCatalogItem):

- шаблоны имени/описания — EquipmentType «Электропривод» (name_template /
  spec_template + *_template_i18n; цепочка TemplateMixin: _get_name_template_source
  → EquipmentType → fallback);
- словарь подстановок — реестр ``ea_catalog_item_fields.py`` (TEMPLATE_FIELDS +
  NAME/CODE/VARS_FIELD_KEYS); сложные значения (сигналы матрицы) — resolver-методы
  ``_res_*`` с локализацией через ``localized_name`` (locale из TemplateMixin);
- артикул — ``model_line.model_item_code_template`` + ext-код
  (property ``generated_ext_code`` переопределён: services.ea_ext_code /
  ea_configurator_data.selection_ext_code из выбранных матричных строк и
  контекста карточки);
- config_hash — ConfigHashMixin (каноническая конфигурация: все опции +
  M2M выбранных матричных строк), коллизия → ValidationError;
- SKU — sync_sku() (SKUMixin);
- каталог = карточки с is_catalog=True (стандартные конфигурации);
  нестандартные (конструктор → корзина) — is_catalog=False.
"""
import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import EquipmentTypeMixin
from core.models.config_hash import ConfigHashMixin
from core.models.mixins import TemplateMixin
from core.utils.localization import localized_name
from options.exd import ChosenExdRowMixin
from sku.models import SKUMixin

from electric_actuators.models.ea_catalog_item_fields import (
    EA_CATALOG_ITEM_TEMPLATE_FIELDS)

logger = logging.getLogger(__name__)

# Роли управляющего сигнала уставки (0-10 В / 4-20 мА) — выводятся отдельным
# плейсхолдером {ctl_setpoint}, а не в {ctl_commands}.
_SETPOINT_ROLES = ('CMD_4_20MA', 'CMD_0_10V')

# Локализованные подписи режима (ru — базовый; en/cn — переводы).
_MODE_LABELS = {
    'on_off': {'ru': 'Двухпозиционный', 'en': 'On-off', 'cn': '两位'},
    'modulating': {'ru': 'Модулирующий', 'en': 'Modulating', 'cn': '调节'},
    'both': {'ru': 'Оба режима', 'en': 'Both modes', 'cn': '两种模式'},
}


class ElectricActuatorCatalogItem(
    EquipmentTypeMixin, ConfigHashMixin, SKUMixin,
    ChosenExdRowMixin, TemplateMixin, models.Model,
):
    """Каталожная карточка исполнения электропривода (эталон каталога)."""

    class Origin(models.TextChoices):
        GENERATED = 'generated', _('Сгенерирована')
        MANUAL = 'manual', _('Ручная')

    # Взрывозащита — общий паттерн (exd-option.md §3.6): выбранная строка
    # серии (FK ``exd``) → кодировка + M2M видов (ChosenExdRowMixin).
    exd_row_field = 'exd'
    exd_through_model = 'electric_actuators.ElectricExdOption'
    exd_parent_field = 'model_line'

    # Реестр полей (единый источник правды) + составы словарей.
    TEMPLATE_FIELDS = EA_CATALOG_ITEM_TEMPLATE_FIELDS
    NAME_FIELD_KEYS = (
        'code', 'series_code', 'body_code', 'torque', 'time_to_close',
        'power_supply', 'voltage',
        'cu_name', 'cu_power_supply', 'cu_mode', 'cu_heater',
        'ctl_protocol', 'ctl_commands', 'ctl_setpoint', 'ctl_local_controls',
        'fb_end_switches', 'fb_way_switches', 'fb_torque_switches',
        'fb_position_feedback', 'fb_hart', 'fb_thermal_sensor',
        'fb_indicator', 'fb_turn_counter',
        'temperature', 'ip', 'exd', 'exd_short', 'coating', 'color',
        'hand_wheel', 'turn_angle', 'cable_glands', 'access_device',
        'safety_position', 'article', 'ext_code',
    )
    CODE_FIELD_KEYS = ('code', 'temperature', 'ip', 'cu_name', 'voltage', 'exd')
    VARS_FIELD_KEYS = (
        'code', 'series_code', 'body_code', 'torque', 'time_to_close',
        'power_supply', 'voltage', 'cu_name', 'cu_power_supply', 'cu_mode',
        'ctl_protocol', 'ctl_commands', 'ctl_setpoint',
        'fb_end_switches', 'fb_way_switches', 'fb_torque_switches',
        'fb_position_feedback', 'fb_hart',
        'temperature', 'ip', 'exd', 'exd_short', 'coating', 'color', 'hand_wheel',
        'turn_angle', 'cable_glands', 'access_device', 'safety_position',
    )

    # Шаблоны имени/описания живут в EquipmentType («Электропривод»), а не
    # на model_line — поэтому серия обязательных полей шаблонов не имеет.
    required_model_line_fields = ()

    # Каноническая конфигурация (порядок важен для хэша)
    config_hash_fields = (
        'model_line', 'body', 'model_line_item', 'power_supply',
        'control_unit', 'mode', 'cu_power_supply', 'temperature', 'ip', 'exd',
        'coating', 'color', 'hand_wheel', 'turn_angle', 'cable_glands',
        'safety_position', 'access_device', 'matrix_rows',
    )

    model_line = models.ForeignKey(
        'ElectricActuatorModelLine', on_delete=models.PROTECT,
        related_name='catalog_items', verbose_name=_("Серия"))
    body = models.ForeignKey(
        'ElectricActuatorBody', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Корпус"))
    model_line_item = models.ForeignKey(
        'ElectricActuatorModelLineItem', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Модель"))
    power_supply = models.ForeignKey(
        'ElectricPowerSupplyOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Напряжение питания"))
    control_unit = models.ForeignKey(
        'params.ControlUnitInstalledOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='ea_catalog_items',
        verbose_name=_("Блок управления"))
    mode = models.CharField(
        max_length=20, default='on_off',
        choices=(('on_off', _('Двухпозиционный')),
                 ('modulating', _('Модулирующий')),
                 ('both', _('Оба режима'))),
        verbose_name=_("Режим"))
    cu_power_supply = models.ForeignKey(
        'params.PowerSupplies', on_delete=models.PROTECT,
        null=True, blank=True, related_name='ea_catalog_cu_power_supplies',
        verbose_name=_("Питание БУ отдельно"))
    temperature = models.ForeignKey(
        'ElectricTemperatureOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Температурная опция"))
    ip = models.ForeignKey(
        'ElectricIpOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Степень защиты IP"))
    exd = models.ForeignKey(
        'ElectricExdOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Взрывозащита"))
    coating = models.ForeignKey(
        'ElectricBodyCoatingOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Покрытие корпуса"))
    color = models.ForeignKey(
        'ElectricBodyColorOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Цвет корпуса"))
    hand_wheel = models.ForeignKey(
        'ElectricHandWheelOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Ручной дублёр"))
    turn_angle = models.ForeignKey(
        'ElectricTurnAngleOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Угол поворота"))
    cable_glands = models.ForeignKey(
        'CableGlandHolesSetBodyOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='ea_catalog_items',
        verbose_name=_("Кабельные вводы"))
    safety_position = models.ForeignKey(
        'ElectricSafetyPositionOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Положение безопасности"))
    access_device = models.ForeignKey(
        'EaAccessDeviceOption', on_delete=models.PROTECT,
        null=True, blank=True, related_name='catalog_items',
        verbose_name=_("Устройство ограничения доступа"))
    matrix_rows = models.ManyToManyField(
        'EaSignalMatrixEntry', blank=True, related_name='catalog_items',
        verbose_name=_("Выбранные сигнальные опции (матрица)"))

    name = models.CharField(max_length=500, blank=True, verbose_name=_("Название"))
    code = models.CharField(max_length=300, blank=True, verbose_name=_("Артикул"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    is_catalog = models.BooleanField(
        default=True, verbose_name=_("В каталоге"),
        help_text=_("Стандартная карточка каталога; нестандартные — False"))
    origin = models.CharField(
        max_length=20, choices=Origin.choices, default=Origin.GENERATED,
        verbose_name=_("Происхождение"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Карточка каталога электропривода")
        verbose_name_plural = _("Карточки каталога электроприводов")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.code or self.name or f'EA item #{self.pk}'

    # ── Источники шаблонов: EquipmentType «Электропривод» (не model_line) ──
    def _get_equipment_type(self):
        """EquipmentType карточки; для несохранённой — по коду
        'electric-actuator' (цепочка миксина: серия → прямое поле)."""
        et = super()._get_equipment_type()
        if et is None:
            from core.models.equipment_type import EquipmentType
            et = EquipmentType.objects.filter(
                code='electric-actuator').first()
        return et

    def _get_name_template_source(self):
        return self._get_equipment_type_template('name_template') or None

    def _get_description_template_source(self):
        # Описание — spec_template EquipmentType (полная спецификация).
        return self._get_equipment_type_template('spec_template') or None

    def _get_template_i18n(self, field_base: str):
        """Переводы шаблонов — с того же EquipmentType (карточка без шаблонов
        на серии; базовый миксин для этого случая i18n не находит).
        Описание рендерится из spec_template → переводы из spec_template_i18n."""
        et = self._get_equipment_type()
        if et is None:
            from core.models.equipment_type import EquipmentType
            et = EquipmentType.objects.filter(
                code='electric-actuator').first()
        if et is None:
            return None
        i18n_field = f'{field_base}_i18n'
        if field_base == 'description_template':
            i18n_field = 'spec_template_i18n'
        return getattr(et, i18n_field, None)

    # ── Ext-код: машинная сборка из матричных строк (не ext-шаблон серии) ──
    @property
    def generated_ext_code(self) -> str:
        """Ext-код из выбранных матричных строк + контекста карточки."""
        from electric_actuators.services.ea_configurator_data import (
            selection_ext_code)
        from electric_actuators.services.ea_ext_code import (
            CU_EXT, PS_EXT, MODE_EXT)
        if not self.model_line_item_id:
            return ''
        context = {}
        if self.control_unit_id:
            context['cu'] = CU_EXT.get(self.control_unit.code, '')
        if self.power_supply_id and self.power_supply.power_supply_id:
            context['ps'] = PS_EXT.get(self.power_supply.power_supply.code, '')
        context['mode'] = MODE_EXT.get(self.mode, '')
        try:
            row_ids = (list(self.matrix_rows.values_list('pk', flat=True))
                       if self.pk else [])
            return selection_ext_code(
                self.model_line_item, row_ids,
                temp_option=self.temperature, context=context)
        except Exception as e:  # noqa: BLE001
            logger.warning('ext-код карточки не собран: %s', e)
            return ''

    def _res_article(self, locale=None) -> str:
        """Полный артикул (шаблон серии + ext-код)."""
        return self.code or self.generated_model_item_code

    def _res_ext_code(self, locale=None) -> str:
        return self.generated_ext_code

    # ── Простые значения (нелокализуемые) ──
    def _res_torque(self, locale=None) -> str:
        mli = self.model_line_item
        return str(mli.torque_max) if mli and mli.torque_max else ''

    def _res_time_to_close(self, locale=None) -> str:
        mli = self.model_line_item
        return str(mli.time_to_close) if mli and mli.time_to_close else ''

    def _res_mode(self, locale=None) -> str:
        labels = _MODE_LABELS.get(self.mode, {'ru': self.mode})
        locale = locale or 'ru'
        return labels.get(locale) or labels['ru']

    # ── Значения из матричных строк (локализованные) ──
    def _matrix_rows(self):
        """Выбранные строки матрицы (пусто для несохранённой карточки)."""
        if not self.pk:
            return []
        return list(self.matrix_rows.select_related(
            'slot', 'option', 'control_signal', 'feedback_signal',
            'protocol', 'device', 'heater_supply').all())

    @staticmethod
    def _join_unique(values):
        return ', '.join(dict.fromkeys(v for v in values if v))

    def _res_protocol(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.protocol, locale) for r in self._matrix_rows()
            if r.protocol_id and r.protocol.name)

    def _res_commands(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.control_signal, locale) for r in self._matrix_rows()
            if r.control_signal_id and r.control_signal.name
            and r.control_signal.role not in _SETPOINT_ROLES)

    def _res_setpoint(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.control_signal, locale) for r in self._matrix_rows()
            if r.control_signal_id and r.control_signal.name
            and r.control_signal.role in _SETPOINT_ROLES)

    def _res_local_controls(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.option, locale) if r.option_id else r.name
            for r in self._matrix_rows()
            if r.slot_id and r.slot.code == 'LOCAL_CONTROL')

    def _res_end_switches(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.feedback_signal, locale)
            for r in self._matrix_rows()
            if r.feedback_signal_id and r.feedback_signal.name
            and r.feedback_signal.role.startswith('END'))

    def _res_way_switches(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.feedback_signal, locale)
            for r in self._matrix_rows()
            if r.feedback_signal_id and r.feedback_signal.name
            and r.feedback_signal.role.startswith('WAY'))

    def _res_torque_switches(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.feedback_signal, locale)
            for r in self._matrix_rows()
            if r.feedback_signal_id and r.feedback_signal.name
            and r.feedback_signal.role.startswith('TORQUE'))

    def _res_position_feedback(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.feedback_signal, locale)
            for r in self._matrix_rows()
            if r.feedback_signal_id and r.feedback_signal.name
            and r.feedback_signal.role == 'POSITION')

    def _res_hart(self, locale=None) -> str:
        return 'HART' if any(
            r.feedback_signal_id and getattr(r.feedback_signal, 'hart', False)
            for r in self._matrix_rows()) else ''

    def _res_thermal_sensor(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.device, locale) for r in self._matrix_rows()
            if r.device_id and r.device.name)

    def _res_cu_heater(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.heater_supply, locale) for r in self._matrix_rows()
            if r.heater_supply_id and r.heater_supply.name)

    def _res_indicator(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.option, locale) if r.option_id else r.name
            for r in self._matrix_rows()
            if r.slot_id and r.slot.code == 'INDICATOR')

    def _res_turn_counter(self, locale=None) -> str:
        return self._join_unique(
            localized_name(r.option, locale) if r.option_id else r.name
            for r in self._matrix_rows()
            if r.slot_id and r.slot.code == 'TURN_COUNTER')

    # ── Сохранение (стандартный цикл каталога) ──
    def save(self, *args, **kwargs):
        """1) equipment_type автозаполняется (серия → код 'electric-actuator');
        2) code автогенерируется из model_line.model_item_code_template + ext;
        3) config_hash пересчитывается; коллизия → ValidationError;
        4) super().save() → TemplateMixin.save() генерирует name/description
           из шаблонов EquipmentType; 5) sync_sku().
        """
        if not self.equipment_type_id:
            et = None
            if self.model_line_id and getattr(self.model_line,
                                              'equipment_type_id', None):
                et = self.model_line.equipment_type
            if et is None:
                from core.models.equipment_type import EquipmentType
                et = EquipmentType.objects.filter(
                    code='electric-actuator').first()
            if et is not None:
                self.equipment_type = et
        if not self.code or self.origin == self.Origin.GENERATED:
            # Сгенерированные карточки: артикул — функция конфигурации,
            # пересобирается при каждом сохранении (смена любой опции FK или
            # M2M меняет артикул). Ручные (origin=manual) — артикул стабилен.
            self.code = self.generated_model_item_code or ''
        self.config_hash = self.compute_config_hash()
        self._check_config_hash_unique()
        super().save(*args, **kwargs)
        self.sync_sku()
