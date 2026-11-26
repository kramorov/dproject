# electric_actuators/models/ea_catalog_item.py
"""
Эталонная каталожная карточка электропривода — ElectricActuatorCatalogItem.

Работает по единому контракту каталога (template_mixin.md, образец —
PneumaticActuatorCatalogItem):

- шаблоны имени/описания — EquipmentType «Электропривод» (name_template /
  spec_template + *_template_i18n; цепочка TemplateMixin: _get_name_template_source
  → EquipmentType → fallback);
- словарь подстановок — реестр ``ea_catalog_item_fields.py`` (TEMPLATE_FIELDS +
  NAME/CODE/VARS_FIELD_KEYS); БУ — ``_res_cu_block``/``_res_cu_description``
  из ``ea_control`` с локализацией через ``localized_name``;
- артикул — ``model_line.model_item_code_template`` + ext-код по
  ``model_line.ext_encoding_template`` (``generated_ext_code`` собирает вклад
  БУ через ``cu_code``);
- config_hash — ConfigHashMixin (каноническая конфигурация: все опции),
  коллизия → ValidationError;
- SKU — sync_sku() (SKUMixin);
- каталог = карточки с is_catalog=True (стандартные конфигурации);
  нестандартные (конструктор → корзина) — is_catalog=False.
"""
import logging
import re

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import EquipmentTypeMixin
from core.models.config_hash import ConfigHashMixin
from core.models.mixins import TemplateMixin
from core.utils.localization import localized_name, pick_i18n
from options.exd import ChosenExdRowMixin
from sku.models import SKUMixin

from electric_actuators.models.ea_catalog_item_fields import (
    EA_CATALOG_ITEM_TEMPLATE_FIELDS)

logger = logging.getLogger(__name__)

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
        'code', 'series_code', 'body_code', 'weight', 'torque', 'time_to_close',
        'power_supply', 'voltage',
        'motor_current_rated', 'motor_current_starting', 'motor_power',
        'cu_name', 'cu_code', 'cu_description', 'cu_block', 'cu_power_supply', 'cu_mode',
        'temperature', 'ip', 'exd', 'exd_short', 'coating', 'color',
        'hand_wheel', 'turn_angle', 'cable_glands', 'access_device',
        'safety_position', 'article', 'ext_code',
    )
    CODE_FIELD_KEYS = ('code', 'temperature', 'ip', 'cu_name', 'voltage', 'exd')
    VARS_FIELD_KEYS = (
        'code', 'series_code', 'body_code', 'weight', 'torque', 'time_to_close',
        'power_supply', 'voltage', 'cu_name', 'cu_code', 'cu_description',
        'cu_power_supply', 'cu_mode',
        'temperature', 'ip', 'exd', 'exd_short', 'coating', 'color', 'hand_wheel',
        'turn_angle', 'cable_glands', 'access_device', 'safety_position',
    )

    # Шаблоны имени/описания живут в EquipmentType («Электропривод»), а не
    # на model_line — поэтому серия обязательных полей шаблонов не имеет.
    required_model_line_fields = ()

    # Каноническая конфигурация (порядок важен для хэша)
    config_hash_fields = (
        'model_line', 'body', 'model_line_item', 'power_supply',
        'control_unit', 'control_unit_snapshot', 'mode', 'cu_power_supply',
        'temperature', 'ip', 'exd',
        'coating', 'color', 'hand_wheel', 'turn_angle', 'cable_glands',
        'safety_position', 'access_device',
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
        'ea_control.ControlUnit', on_delete=models.PROTECT,
        null=True, blank=True, related_name='ea_catalog_items',
        verbose_name=_("Блок управления"),
        help_text=_("Выбранный тип БУ из ea_control; внутренняя конфигурация "
                    "слотов — control_unit_snapshot"))
    control_unit_snapshot = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Снимок конфигурации БУ"),
        help_text=_("Выбранные опции слотов БУ: {slot_code: option_code}"))
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
        # Описание — из EquipmentType «Электропривод» (унификация, как и name_template).
        return self._get_equipment_type_template('description_template') or None

    def _get_template_i18n(self, field_base: str):
        """Переводы шаблонов — из EquipmentType «Электропривод» (унификация).

        Для spec_title/list_title при пустом RU-шаблоне — фолбэк на title_template
        (как в базовом TemplateMixin).
        """
        et = self._get_equipment_type()
        if et is None:
            from core.models.equipment_type import EquipmentType
            et = EquipmentType.objects.filter(
                code='electric-actuator').first()
        if et is None:
            return None
        if field_base in ('spec_title_template', 'list_title_template') and not getattr(et, field_base, None):
            return getattr(et, 'title_template_i18n', None)
        return getattr(et, f'{field_base}_i18n', None)

    # ── Ext-код: машинная сборка по model_line.ext_encoding_template ──
    @property
    def generated_ext_code(self) -> str:
        """Ext-часть артикула по шаблону ``model_line.ext_encoding_template``.

        Аналог ``ElectricActuatorConstructor.generated_ext_code``: сигнальные
        позиции (end/way/torq/pos/hart/lc/cmd/setp/cnt/ind) пусты — сигналы
        БУ теперь в ``cu_block``/``cu_code``.
        """
        if not self.model_line_id:
            return ''
        template = self.model_line.ext_encoding_template
        if not template:
            return ''
        result = template
        result = result.replace('{temperature_e_enc}',
                                self.temperature.ext_encoding or '' if self.temperature_id else '')
        result = result.replace('{ip_e_enc}',
                                self.ip.ext_encoding or '' if self.ip_id else '')
        result = result.replace('{voltage_e_enc}',
                                self.power_supply.ext_encoding or '' if self.power_supply_id else '')
        result = result.replace('{exd_e_enc}',
                                self.exd.ext_encoding or '' if self.exd_id else '')
        result = result.replace('{control_unit_e_enc}', self._cu_ext_code())
        result = result.replace('{cu_e_enc}', self._cu_ext_code())
        result = result.replace('{cu_p_e_enc}', '')
        result = result.replace('{ps_e_enc}', self._ps_ext())
        result = result.replace('{mode_e_enc}', '')
        result = result.replace('{proto_e_enc}', '')
        result = result.replace('{end_e_enc}', '')
        result = result.replace('{way_e_enc}', '')
        result = result.replace('{torq_e_enc}', '')
        result = result.replace('{pos_e_enc}', '')
        result = result.replace('{hart_e_enc}', '')
        result = result.replace('{temp_e_enc}', self._temp_ext())
        result = result.replace('{sp_e_enc}', self._sp_ext())
        result = result.replace('{ad_e_enc}', self._ad_ext())
        result = result.replace('{access_device_e_enc}', self._ad_ext())
        result = result.replace('{h_cu_e_enc}', '')
        result = result.replace('{therm_e_enc}', '')
        result = result.replace('{lc_e_enc}', '')
        result = result.replace('{cmd_e_enc}', '')
        result = result.replace('{setp_e_enc}', '')
        result = result.replace('{cnt_e_enc}', '')
        result = result.replace('{ind_e_enc}', '')
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\.\s+', ' ', result)
        result = re.sub(r'\(\s*\)', '', result)
        result = re.sub(r'-\.', '.', result)
        result = re.sub(r'\.-', '.', result)
        result = re.sub(r'\s{2,}', ' ', result)
        result = re.sub(r'[.-]+$', '', result)
        result = re.sub(r'^[.\-\s]+', '', result)
        return result.strip()

    def _ps_ext(self) -> str:
        """ext-код напряжения мотора (''/220AC/380AC/24DC)."""
        from electric_actuators.services.ea_ext_code import PS_EXT
        if self.power_supply_id and self.power_supply.power_supply_id:
            return PS_EXT.get(self.power_supply.power_supply.code, '')
        return ''

    def _temp_ext(self) -> str:
        """ext-код температуры/обогрева привода (''/L/LM/V/VM)."""
        from electric_actuators.services.ea_ext_code import TEMP_BASE
        t = self.temperature
        if not t:
            return ''
        base = TEMP_BASE.get(t.code or '', '')
        if base and t.heater_supply_id and t.heater_supply.code == 'MOTOR_CIRCUIT':
            base = base + 'M'
        return base

    def _sp_ext(self) -> str:
        """ext-код положения безопасности: FL/NC/NO/BAT."""
        from electric_actuators.services.ea_ext_code import SP_EXT
        sp = self.safety_position
        if not sp or not sp.safety_position_id:
            return 'FL'
        return SP_EXT.get(sp.safety_position.code, 'FL')

    def _ad_ext(self) -> str:
        """ext-код устройства ограничения доступа: AD0 — нет, AD1 — есть."""
        from electric_actuators.services.ea_ext_code import AD_EXT
        if not self.access_device_id:
            return 'AD0'
        return AD_EXT.get(self.access_device.code, 'AD0')

    def _cu_ext_code(self) -> str:
        """Вклад БУ в ext-код (новая слотовая схема, ea_control.cu_code)."""
        from ea_control.services.cu_code import build_ext_article_code
        ps = (self.power_supply.power_supply
              if self.power_supply_id and self.power_supply else None)
        return build_ext_article_code(
            self.control_unit,
            snapshot=self.control_unit_snapshot or None,
            power_supply=ps, mode=self.mode,
            model_line=self.model_line, body=self.body,
            model_line_item=self.model_line_item) or ''

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
        if not mli:
            return ''
        # если время закрытия не задано (0), берём время открытия — в большинстве
        # случаев они совпадают, в данных заполнено одно из двух.
        value = mli.time_to_close or mli.time_to_open
        if not value:
            return ''
        return str(value).rstrip('0').rstrip('.')

    def _res_mode(self, locale=None) -> str:
        labels = _MODE_LABELS.get(self.mode, {'ru': self.mode})
        locale = locale or 'ru'
        return labels.get(locale) or labels['ru']

    def _res_cu_block(self, locale=None) -> str:
        """Блок описания БУ (слотовая модель) — генератор ea_control.

        Каталожная карточка берёт описание БУ из ``cu_description``
        (видимость по правилам, значения из снимка/дефолтов) — не дублирует
        его в legacy-матрице.
        """
        if not self.control_unit_id:
            return ''
        from ea_control.services.cu_description import build_description
        ps = (self.power_supply.power_supply
              if self.power_supply_id and self.power_supply else None)
        try:
            return build_description(
                self.control_unit,
                snapshot=self.control_unit_snapshot or None,
                power_supply=ps, mode='both', locale=locale,
                include_name=False)
        except Exception:  # noqa: BLE001
            logger.exception('Ошибка генерации блока описания БУ')
            return ''

    def _res_cu_description(self, locale=None) -> str:
        """Описание типа БУ (локализованное) — из ControlUnit."""
        if not self.control_unit_id:
            return ''
        cu = self.control_unit
        return pick_i18n(cu.description_i18n, locale,
                         fallback=cu.description or '')

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
