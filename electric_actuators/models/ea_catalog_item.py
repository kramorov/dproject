# electric_actuators/models/ea_catalog_item.py
"""
Эталонная каталожная карточка электропривода — ElectricActuatorCatalogItem.

Работает по контракту каталога (образец — PneumaticActuatorCatalogItem):

- config_hash_fields — каноническая конфигурация (все опции + M2M выбранных
  матричных строк) → SHA-256 (ConfigHashMixin); M2M пересчитывается ресивером
  m2m_changed (core/apps.py);
- имя/описание — из шаблонов EquipmentType «Электропривод» (name_template /
  spec_template + *_template_i18n, локализация);
- артикул (code) — model_line.model_item_code_template + ext-код
  (services/ea_ext_code.build_ext_code из выбранных матричных строк и
  контекста: cu/cu_p/ps/mode/temp/ip/exd/sp/ad);
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
from sku.models import SKUMixin

logger = logging.getLogger(__name__)


class ElectricActuatorCatalogItem(
    EquipmentTypeMixin, ConfigHashMixin, SKUMixin, TemplateMixin, models.Model,
):
    """Каталожная карточка исполнения электропривода (эталон каталога)."""

    class Origin(models.TextChoices):
        GENERATED = 'generated', _('Сгенерирована')
        MANUAL = 'manual', _('Ручная')

    # Каноническая конфигурация (порядок важен для хэша)
    config_hash_fields = (
        'model_line', 'body', 'model_line_item', 'power_supply',
        'control_unit', 'mode', 'cu_power_supply', 'temperature', 'ip', 'exd',
        'coating', 'color', 'hand_wheel', 'turn_angle', 'cable_glands',
        'safety_position', 'access_device', 'matrix_rows',
    )

    # Шаблоны имени/описания живут в EquipmentType («Электропривод»),
    # а не на model_line (см. update_name/update_description).
    required_model_line_fields = ()

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

    # ── Шаблоны: источник — EquipmentType «Электропривод» ──
    def _get_equipment_type(self):
        from core.models.equipment_type import EquipmentType
        return EquipmentType.objects.filter(code='electric-actuator').first()

    def equipment_type_or_default(self):
        et = getattr(self, 'equipment_type', None)
        if et is not None and et.pk:
            return et
        return self._get_equipment_type()

    def _et_name_template(self):
        et = self.equipment_type_or_default()
        return et.name_template if et else ''

    def _et_spec_template(self):
        et = self.equipment_type_or_default()
        return et.spec_template if et else ''

    def _flat_data(self):
        """Плейсхолдеры шаблонов → готовые строки (ru)."""
        mli = self.model_line_item
        ps = self.power_supply
        cu = self.control_unit
        temp = self.temperature
        sp = self.safety_position
        rows = list(self.matrix_rows.select_related(
            'slot', 'feedback_signal', 'control_signal')) if self.pk else []
        by_slot = {}
        for r in rows:
            by_slot.setdefault(r.slot.code if r.slot_id else '?', []).append(r)
        return {
            'series_code': self.model_line.code or '' if self.model_line_id else '',
            'model_code': (mli.code or mli.name) if mli else '',
            'body_code': (self.body.code or self.body.name) if self.body_id else '',
            'torque': str(mli.torque_max) if mli and mli.torque_max else '',
            'time_to_close': str(mli.time_to_close) if mli and mli.time_to_close else '',
            'power_supply': str(ps.power_supply) if ps and ps.power_supply_id else '',
            'control_unit': cu.name if cu else '',
            'cu_power_supply': str(self.cu_power_supply) if self.cu_power_supply_id else '',
            'mode': dict(self._meta.get_field('mode').choices).get(self.mode, self.mode),
            'temperature': str(temp) if temp else '',
            'ip': str(self.ip) if self.ip_id else '',
            'exd': (self.exd.exd_short or self.exd.encoding) if self.exd_id else '',
            'coating': str(self.coating) if self.coating_id else '',
            'color': str(self.color) if self.color_id else '',
            'hand_wheel': str(self.hand_wheel) if self.hand_wheel_id else '',
            'turn_angle': str(self.turn_angle) if self.turn_angle_id else '',
            'cable_glands': str(self.cable_glands) if self.cable_glands_id else '',
            'access_device': self.access_device.name if self.access_device_id else '',
            'safety_position': (sp.safety_position.name
                                if sp and sp.safety_position_id else ''),
            'protocol': ', '.join(r.protocol.name for r in rows if r.protocol_id),
            'commands': ', '.join(r.control_signal.name for r in rows
                                  if r.control_signal_id),
            'setpoint': ', '.join(r.control_signal.name for r in rows
                                  if r.control_signal_id
                                  and r.control_signal.role == 'CMD_4_20MA'),
            'end_switches': ', '.join(r.feedback_signal.name for r in rows
                                      if r.feedback_signal_id
                                      and r.feedback_signal.role.startswith('END')),
            'way_switches': ', '.join(r.feedback_signal.name for r in rows
                                      if r.feedback_signal_id
                                      and r.feedback_signal.role.startswith('WAY')),
            'torque_switches': ', '.join(r.feedback_signal.name for r in rows
                                         if r.feedback_signal_id
                                         and r.feedback_signal.role.startswith(
                                             'TORQUE')),
            'position_feedback': ', '.join(r.feedback_signal.name for r in rows
                                           if r.feedback_signal_id
                                           and r.feedback_signal.role == 'POSITION'),
            'hart': 'HART' if any(getattr(r.feedback_signal, 'hart', False)
                                  for r in rows if r.feedback_signal_id) else '',
            'heater_cu': ', '.join(r.heater_supply.name for r in rows
                                   if r.heater_supply_id),
            'thermal_sensor': ', '.join(r.device.name for r in rows
                                        if r.device_id),
            'local_control': '',
            'indicator': '',
            'turn_counter': '',
            'article': self.code or '',
            'ext_code': (self.generated_ext_code()
                         if self.pk and self.model_line_item_id else ''),
        }

    def generated_ext_code(self):
        """Ext-код из выбранных матричных строк + контекста карточки."""
        from electric_actuators.services.ea_configurator_data import (
            selection_ext_code)
        from electric_actuators.services.ea_ext_code import (
            CU_EXT, PS_EXT, MODE_EXT)
        context = {}
        if self.control_unit_id:
            context['cu'] = CU_EXT.get(self.control_unit.code, '')
        if self.power_supply_id and self.power_supply.power_supply_id:
            context['ps'] = PS_EXT.get(self.power_supply.power_supply.code, '')
        context['mode'] = MODE_EXT.get(self.mode, '')
        if self.model_line_item_id:
            try:
                row_ids = (list(self.matrix_rows.values_list(
                    'pk', flat=True)) if self.pk else [])
                return selection_ext_code(
                    self.model_line_item, row_ids,
                    temp_option=self.temperature, context=context)
            except Exception as e:  # noqa: BLE001
                logger.warning('ext-код карточки не собран: %s', e)
        return ''

    def generated_article(self):
        """Артикул: основной шаблон + ext-код."""
        base = ''
        if self.model_line_id and self.model_line.model_item_code_template:
            t = self.model_line.model_item_code_template
            d = self._flat_data()
            d['temperature'] = (self.temperature.encoding or ''
                                if self.temperature_id else '')
            d['ip'] = (self.ip.encoding or '' if self.ip_id else '')
            d['exd'] = (self.exd.encoding or '' if self.exd_id else '')
            d['voltage'] = (self.power_supply.encoding or ''
                            if self.power_supply_id else '')
            d['control_unit'] = (self.control_unit.code if self.control_unit_id
                                 else '')
            d['model_code'] = (self.model_line_item.code or ''
                               if self.model_line_item_id else '')
            for k, v in d.items():
                t = t.replace('{%s}' % k, str(v or ''))
            base = t.strip(' .')
        ext = self.generated_ext_code()
        return (base + ' ' + ext).strip() if ext else base

    # ── Генерация имени/описания из шаблонов EquipmentType ──
    def _fill_simple(self, template):
        result = template or ''
        for k, v in self._flat_data().items():
            result = result.replace('{%s}' % k, str(v or ''))
        return result.strip()

    def update_name(self, save=False):
        tpl = self._et_name_template()
        if tpl:
            self.name = self._fill_simple(tpl)
            return True
        return False

    def update_description(self, save=False):
        tpl = self._et_spec_template()
        if tpl:
            self.description = self._fill_simple(tpl)
            return True
        return False

    def save(self, *args, **kwargs):
        skip_auto_generate = kwargs.pop('skip_auto_generate', False)
        et = self.equipment_type_or_default()
        if et is not None and (not self.equipment_type_id):
            self.equipment_type = et
        if not skip_auto_generate:
            self.update_name(save=False)
            self.update_description(save=False)
        if not self.code:
            self.code = self.generated_article()
        self.config_hash = self.compute_config_hash()
        self._check_config_hash_unique()
        super().save(*args, **kwargs)
        self.sync_sku()
