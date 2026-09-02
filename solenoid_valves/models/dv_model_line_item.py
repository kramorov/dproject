# solenoid_valves/models/dv_model_line_item.py

from django.db import models
import math
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any

from core.models import StructuredDataMixin, EquipmentTypeMixin, TechDocMixin, ImageGalleryMixin
from core.models.mixins import TemplateMixin, CatalogDictMixin, CopyMixin
# TemplateGeneratorMixin удалён 2026-09-01 — DirectionValve использует единый TemplateMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin

from .dv_model_line import DirectionalValveModelLine
from .dv_body import DirectionValveBody
from .sv_options import ValveFunction, ValveActuationVariety, ManualOverride
from materials.models import MaterialGeneral, MaterialSpecified
from params.models import PowerSupplies, PneumaticConnection, ThreadSize
from producers.models import Brands, Producer
from electric_actuators.models import CableGlandHolesSet
from sku.models import SKUMixin
class DirectionValve(CatalogDictMixin,
                     ImageGalleryMixin,
                     TechDocMixin,
                     SKUMixin, CopyMixin, TemplateMixin,
                     SmartCatalogMixin, EquipmentTypeMixin, models.Model):
    """
    Распределительный клапан (конкретный артикул каталога).

    Определяет финальный Part Number и цену. Связан с DirectionalValveModelLine
    (серия/DNA клапана) и DirectionValveBody (корпус).

    Наследует:
      - SmartCatalogMixin — фильтрация, поиск, exact/compatible split
      - CatalogDictMixin — структурированная сериализация (to_dict/to_values_dict)
      - ImageGalleryMixin — галерея изображений
      - TechDocMixin — техническая документация
      - TemplateMixin — шаблоны названий/описаний (единый контракт)
      - SKUMixin — учётная номенклатура
      - CopyMixin — копирование в админке
      - EquipmentTypeMixin — тип оборудования

    Основные поля:
      - function: ValveFunction (3/2, 5/2, 5/3)
      - actuation: ValveActuationVariety (моно/бистабильный)
      - manual_override: ManualOverride (ручной дублёр)
      - body: DirectionValveBody (корпус, вес, KB, пневмоприсоединения)
      - kv, dn: пропускная способность
      - pressure_min/max, work_temp_min/max, medium_density_max: рабочие параметры
      - power_supply, power_consumption_*: электрические характеристики
      - body_material, sealing, solenoid_body_material: материалы
      - ip, exd: защита
      - pneumatic_connection, pneumatic_connection_thread, cable_glands_holes: присоединения
    """

    name = models.TextField(
        verbose_name=_("Название"),
        help_text=_('Текстовое название клапана'))
    code = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код клапана"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание разновидности клапана'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    model_line = models.ForeignKey(DirectionalValveModelLine, related_name='direction_valve_model_line', blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия клапана'),
                                   verbose_name=_("Серия"))
    producer = models.ForeignKey(Producer, related_name='direction_valve_producer', blank=True,
                                 null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Производитель клапана'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, related_name='direction_valve_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд клапанов'),
                              verbose_name=_("Бренд"))

    function = models.ForeignKey(ValveFunction,
                                 related_name='direction_valve_function',
                                 blank=True,
                                 null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Схема (Функция)'),
                                 verbose_name=_("Схема (Функция) клапана"))
    ip = models.ForeignKey('params.IpOption', blank=True, null=True, default=65,
                           on_delete=models.SET_NULL, related_name='direction_valve_ip', verbose_name=_("IP"),
                           help_text=_('Степень IP для модели клапана'))
    exd = models.ForeignKey('params.ExdOption', blank=True, null=True,
                            related_name='direction_valve_exd',
                            on_delete=models.SET_NULL, verbose_name=_("Exd"),
                            help_text=_('Степень взрывозащиты для модели клапана'))
    actuation = models.ForeignKey(ValveActuationVariety,
                                  related_name='direction_valve_actuation',
                                  blank=True,
                                  null=True,
                                  on_delete=models.SET_NULL,
                                  help_text=_('Управление'),
                                  verbose_name=_("Вариант управления"))
    manual_override = models.ForeignKey(ManualOverride,
                                        related_name='direction_valve_manual_override',
                                        blank=True,
                                        null=True,
                                        on_delete=models.SET_NULL,
                                        help_text=_('Ручной дублер'),
                                        verbose_name=_("Ручной дублер"))

    body = \
        models.ForeignKey(DirectionValveBody, blank=True, null=True,
                          related_name='direction_valve_body',
                          on_delete=models.SET_NULL,
                          help_text=_('Корпус'),
                          verbose_name=_("Корпус модели клапана"))

    kv = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                             null=True, help_text=_('Kv, м3/ч'),
                             verbose_name=_("Kv, м3/ч"))
    dn = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                             null=True, help_text=_('Dn'),
                             verbose_name=_("Диаметр, мм"))
    power_supply = models.ForeignKey(PowerSupplies,
                                     related_name='direction_valve_power_supply',
                                     blank=True,
                                     null=True,
                                     on_delete=models.SET_NULL,
                                     help_text=_('Напряжение'),
                                     verbose_name=_("Напряжение питания"))
    power_consumption_start = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                                  null=True, help_text=_('Мощность хол, Вт'),
                                                  verbose_name=_("Мощность пусковая, Вт"))
    power_consumption_hot = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                                null=True, help_text=_('Мощность ном, Вт'),
                                                verbose_name=_("Мощность номинальная, Вт"))
    power_consumption_hold = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                                 null=True, help_text=_('Мощность удерж, Вт'),
                                                 verbose_name=_("Мощность удержания, Вт"))
    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    medium_density_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                             null=True, help_text=_('Вязкость среды, сСт'),
                                             verbose_name=_("Вязкость среды, сСт (мм2/с)"))
    pressure_min = models.DecimalField(decimal_places=2, max_digits=6,
                                       null=True, blank=True, default=0,
                                       help_text=_('Минимальное рабочее давление, бар'),
                                       verbose_name=_('P раб.мин, бар'))

    pressure_max = models.DecimalField(decimal_places=2, max_digits=6,
                                       null=True, blank=True, default=40,
                                       help_text=_('Максимальное рабочее давление, бар'),
                                       verbose_name=_('P раб.макс, бар'))
    # Материалы
    body_material = models.ForeignKey(MaterialGeneral, related_name='direction_valve_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    body_material_specified = models.ForeignKey(MaterialSpecified,
                                                related_name='direction_valve_body_material_specified',
                                                blank=True, null=True,
                                                on_delete=models.SET_NULL,
                                                help_text=_('Материал корпуса арматуры'),
                                                verbose_name=_('Материал корпуса'))
    sealing_material_specified = models.ForeignKey(MaterialSpecified,
                                                   related_name='direction_valve_sealing_material_specified',
                                                   blank=True,
                                                   null=True,
                                                   on_delete=models.SET_NULL,
                                                   help_text=_('Уплотнение'),
                                                   verbose_name=_('Материал уплотнения'))

    solenoid_body_material = models.ForeignKey(MaterialGeneral, related_name='direction_valve_solenoid_body_material',
                                               blank=True,
                                               null=True,
                                               on_delete=models.SET_NULL,
                                               help_text=_('Тип материала соленоида'),
                                               verbose_name=_('Тип материала соленоида'))
    solenoid_body_material_specified = models.ForeignKey(MaterialGeneral,
                                                         related_name='direction_valve_solenoid_body_material_specified',
                                                         blank=True,
                                                         null=True,
                                                         on_delete=models.SET_NULL,
                                                         help_text=_('Материал соленоида'),
                                                         verbose_name=_('Материал соленоида'))

    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                 null=True, help_text=_('Вес'),
                                 verbose_name=_("Вес, кг"))
    pneumatic_connection_thread = models.ForeignKey(ThreadSize, on_delete=models.SET_NULL, null=True, blank=True,
                                                    related_name='direction_valve_body_thread',
                                                    verbose_name=_("Пневмовыход"),
                                                    help_text=_('Резьба выходного отверстия для пневмоподключения'))
    pneumatic_connection = models.ForeignKey(
        PneumaticConnection,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='direction_valve_pneumatic_connection',
        verbose_name=_("Пневмоприсоединение"),
        help_text=_('Тип пневмоприсоединений'))
    cable_glands_holes = \
        models.ForeignKey(CableGlandHolesSet, null=True, blank=True,
                          related_name='direction_valve_cable_glands_holes',
                          on_delete=models.SET_NULL, verbose_name=_("Отверстия КВ"),
                           help_text=_('Отверстия под кабельные вводы'))

    def save(self, *args, **kwargs):
        """Сохраняет модель и синхронизирует номенклатуру (SKU)."""
        super().save(*args, **kwargs)
        self.sync_sku()

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Распределительный клапан')
        verbose_name_plural = _('Распределительные клапаны')

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — берётся из model_line."""
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        """Бренд для SKU — берётся из model_line."""
        return self.model_line.brand if self.model_line else None

    @property
    def operation(self):
        """Принцип действия клапана"""
        return str(self.model_line.operation) if self.model_line else ''

    @property
    def construction(self):
        """Тип конструкции клапана"""
        return str(self.model_line.construction) if self.model_line else ''

    @property
    def solenoid_insulation_class(self):
        """Класс изоляции соленоида"""
        return str(self.model_line.solenoid_insulation_class) if self.model_line else ''

    @property
    def working_medium(self):
        """Рабочая среда"""
        return str(self.model_line.working_medium) if self.model_line else ''

    @property
    def temperature_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.work_temp_min}..{self.work_temp_max}'

    @property
    def pressure_range_display(self):
        """Отображаемый диапазон давлений"""
        return f'{self.pressure_min}..{self.pressure_max}'

    def _get_default_name_template(self) -> str:
        default_name_template = "{model_code} Пневмораспределитель {brand} {function} {operation} {actuation}; {pneumatic_connection}; {pneumatic_connection_thread}; корпус: {body_material};  катушка: {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; P {pressure_range} бар; T {temperature_range}°С;  {exd}; {ip}; {power_supply};"
        return default_name_template

    def _get_default_description_template(self) -> str:
        default_description_template = "{model_code} Пневмораспределитель {brand} {operation} {construction} функция {function}; тип пневмоприсоединения - {pneumatic_connection}; присоединение {pneumatic_connection_thread}; Kv-{kv} м3/ч; корпус {body_material}({body_material_specified}); катушка {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; Давление {pressure_range} бар; Темп.окр.среды {temperature_range}°С; отверстие под кабельный ввод {cable_glands_holes},  взрывозащита {exd}; {ip}; Dn {dn} мм; Питание {power_supply}; Мощность холодного/ном/удерж: {power_consumption_start} /  {power_consumption_hot} / {power_consumption_hold}, Вт; Ручной дублер: {manual_override}; макс. плотность рабочей среды {medium_density_max} сСт (мм2/с); Класс изоляции соленоида: {solenoid_insulation_class}; макс 5 циклов/сек; вес {weight}"
        return default_description_template

    def _get_title_template_source(self):
        """Переопределить в модели: вернуть шаблон заголовка или None."""
        title_template = "{model_code} {function}; {temperature_range}°С; {exd}; {ip}; {power_supply}; {operation}; {construction}"
        return title_template

    def _get_name_template_source(self):
        """Шаблон названия из model_line (единый контракт, 2026-09-01)."""
        if not self.model_line:
            return None
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Шаблон описания из model_line (единый контракт, 2026-09-01)."""
        if not self.model_line:
            return None
        return self.model_line.description_template or None
    # Замена переменных
    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{function}': 'function',
            '{operation}': 'operation',
            '{actuation}': 'actuation',
            '{construction}': 'construction',
            '{solenoid_insulation_class}': 'solenoid_insulation_class',
            '{pneumatic_connection}': 'pneumatic_connection',
            '{pneumatic_connection_thread}': 'pneumatic_connection_thread',
            '{kv}': 'kv',
            '{body_material}': 'body_material',
            '{body_material_specified}': 'body_material_specified',
            '{solenoid_body_material}': 'solenoid_body_material',
            '{solenoid_body_material_specified}': 'solenoid_body_material_specified',
            '{sealing_material_specified}': 'sealing_material_specified',
            '{pressure_min}': 'pressure_min',
            '{pressure_max}': 'pressure_max',
            '{dn}': 'dn',
            '{power_supply}': 'power_supply',
            '{power_consumption_start}': 'power_consumption_start',
            '{power_consumption_hot}': 'power_consumption_hot',
            '{power_consumption_hold}': 'power_consumption_hold',
            '{medium_density_max}': 'medium_density_max',
            '{working_medium}': 'working_medium',
            '{manual_override}': 'manual_override',
            '{temperature_range}': 'temperature_range_display',
            '{pressure_range}': 'pressure_range_display',
            '{weight}': 'weight',
            '{cable_glands_holes}': 'cable_glands_holes',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
            '{exd}': 'exd',
            '{ip}': 'ip',
        }

    # ═══════════════════════════════════════════════════════════════
    # CatalogDictMixin — to_dict / to_values_dict / helpers
    # ═══════════════════════════════════════════════════════════════

    def _get_template_vars(self) -> Dict[str, str]:
        """Единый источник строковых значений для UI и шаблонов."""
        return {
            'code': self.code or '',
            'name': self.name or '',
            'model_line_name': self.model_line.name if self.model_line else '',
            'brand_name': self.brand.name if self.brand else '',
            'function': self.function.name if self.function else '',
            'actuation': self.actuation.name if self.actuation else '',
            'construction': self.construction if self.model_line else '',
            'operation': self.operation if self.model_line else '',
            'working_medium': self.working_medium if self.model_line else '',
            'solenoid_insulation_class': self.solenoid_insulation_class if self.model_line else '',
            'manual_override': self.manual_override.name if self.manual_override else '',
            'kv': str(self.kv) if self.kv else '',
            'dn': str(self.dn) if self.dn else '',
            'ip': self.ip.name if self.ip else '',
            'exd': self.exd.name if self.exd else '',
            'power_supply': self.power_supply.name if self.power_supply else '',
            'power_consumption_start': str(self.power_consumption_start) if self.power_consumption_start else '',
            'power_consumption_hot': str(self.power_consumption_hot) if self.power_consumption_hot else '',
            'power_consumption_hold': str(self.power_consumption_hold) if self.power_consumption_hold else '',
            'body_material': self.body_material.name if self.body_material else '',
            'body_material_specified': self.body_material_specified.name if self.body_material_specified else '',
            'sealing_material_specified': self.sealing_material_specified.name if self.sealing_material_specified else '',
            'solenoid_body_material': self.solenoid_body_material.name if self.solenoid_body_material else '',
            'solenoid_body_material_specified': self.solenoid_body_material_specified.name if self.solenoid_body_material_specified else '',
            'pneumatic_connection': self.pneumatic_connection.name if self.pneumatic_connection else '',
            'pneumatic_connection_thread': self.pneumatic_connection_thread.name if self.pneumatic_connection_thread else '',
            'cable_glands_holes': str(self.cable_glands_holes) if self.cable_glands_holes else '',
            'pressure_min': str(self.pressure_min) if self.pressure_min else '',
            'pressure_max': str(self.pressure_max) if self.pressure_max else '',
            'medium_density_max': str(self.medium_density_max) if self.medium_density_max else '',
            'weight': str(self.weight) if self.weight else '',
            'work_temp_min': str(self.work_temp_min) if self.work_temp_min is not None else '',
            'work_temp_max': str(self.work_temp_max) if self.work_temp_max is not None else '',
            'temperature_range': self.temperature_range_display or '',
            'pressure_range': self.pressure_range_display or '',
        }

    def _get_image_alt(self) -> str:
        parts = []
        if self.model_line:
            parts.append(self.model_line.name)
        if self.function:
            parts.append(self.function.name)
        if self.code:
            parts.append(self.code)
        return ' '.join(parts) or self.name or ''

    def _get_docs_section(self) -> list:
        """Техдокументация — инлайн по образцу LimitSwitchBox."""
        docs = []
        seen = set()
        for doc in self.tech_docs.all():
            if doc.id not in seen:
                seen.add(doc.id)
                has_email = doc.variants.filter(role='email').exists()
                docs.append({
                    'id': doc.id,
                    'name': getattr(doc, 'name', '') or '',
                    'url': f"/api/media/{doc.id}/download/",
                    'file_name': getattr(doc, 'file_name', '') or '',
                    'preview_url': f"/api/media/{doc.id}/view/",
                    'email_url': f"/api/media/{doc.id}/download/?variant=email" if has_email else None,
                })
        if self.model_line and hasattr(self.model_line, 'tech_docs'):
            for doc in self.model_line.tech_docs.all():
                if doc.id not in seen:
                    seen.add(doc.id)
                    has_email = doc.variants.filter(role='email').exists()
                    docs.append({
                        'id': doc.id,
                        'name': getattr(doc, 'name', '') or '',
                        'url': f"/api/media/{doc.id}/download/",
                        'file_name': getattr(doc, 'file_name', '') or '',
                        'preview_url': f"/api/media/{doc.id}/view/",
                        'email_url': f"/api/media/{doc.id}/download/?variant=email" if has_email else None,
                    })
        return docs

    def _get_certs_section(self) -> list:
        import re
        certs = []
        if not (self.model_line and hasattr(self.model_line, 'cert_docs')):
            return certs
        for cert in self.model_line.cert_docs.select_related('media_item', 'cert_variety').all():
            try:
                media = getattr(cert, 'media_item', None)
                if not media:
                    continue
                has_email = media.variants.filter(role='email').exists()
                variety_name = str(cert.cert_variety) if cert.cert_variety else ''
                ml_name = self.model_line.name if self.model_line else ''
                code = getattr(cert, 'code', '') or ''
                base_name = re.sub(r'[\\/*?:"<>|]', '_', f"{variety_name} {code} для {ml_name}".strip())
                dl_name = f"{base_name}.pdf"
                email_name = f"{base_name} (сжат).pdf"
                from urllib.parse import quote
                certs.append({
                    'id': media.id,
                    'name': getattr(cert, 'name', '') or '',
                    'file_name': dl_name,
                    'email_file_name': email_name,
                    'url': f"/api/media/{media.id}/download/?filename={quote(dl_name)}",
                    'preview_url': f"/api/media/{media.id}/view/",
                    'email_url': f"/api/media/{media.id}/download/?variant=email&filename={quote(email_name)}" if has_email else None,
                })
            except Exception:
                continue
        return certs

    def to_dict(self) -> Dict[str, Any]:
        tv = self._get_template_vars()
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title() or self.name or '',
            'description': self.description or '',
            'image_alt': self._get_image_alt(),
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
            'template_vars': tv,
            'sections': [
                {
                    'key': 'images',
                    'title': str(_('Изображения')),
                    'type': 'gallery',
                    'order': 1,
                    'data': self._get_images_section(),
                },
                {
                    'key': 'specs',
                    'title': str(_('Характеристики')),
                    'type': 'specs',
                    'order': 2,
                    'groups': [
                        {
                            'key': 'general',
                            'title': str(_('Основные')),
                            'order': 1,
                            'fields': [
                                {'key': 'model_line_name', 'label': str(_('Серия')), 'value': tv['model_line_name'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'brand_name', 'label': str(_('Бренд')), 'value': tv['brand_name'], 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'function', 'label': str(_('Схема')), 'value': tv['function'], 'unit': '', 'type': 'text', 'order': 3},
                                {'key': 'actuation', 'label': str(_('Управление')), 'value': tv['actuation'], 'unit': '', 'type': 'text', 'order': 4},
                                {'key': 'construction', 'label': str(_('Конструкция')), 'value': tv['construction'], 'unit': '', 'type': 'text', 'order': 5},
                                {'key': 'operation', 'label': str(_('Принцип действия')), 'value': tv['operation'], 'unit': '', 'type': 'text', 'order': 6},
                                {'key': 'manual_override', 'label': str(_('Ручной дублер')), 'value': tv['manual_override'], 'unit': '', 'type': 'text', 'order': 7},
                                {'key': 'working_medium', 'label': str(_('Рабочая среда')), 'value': tv['working_medium'], 'unit': '', 'type': 'text', 'order': 8},
                            ]
                        },
                        {
                            'key': 'flow',
                            'title': str(_('Пропускная способность')),
                            'order': 2,
                            'fields': [
                                {'key': 'kv', 'label': 'Kv', 'value': tv['kv'], 'unit': str(_('м³/ч')), 'type': 'number', 'order': 1},
                                {'key': 'dn', 'label': 'DN', 'value': tv['dn'], 'unit': str(_('мм')), 'type': 'number', 'order': 2},
                            ]
                        },
                        {
                            'key': 'pressure',
                            'title': str(_('Давление')),
                            'order': 3,
                            'fields': [
                                {'key': 'pressure_min', 'label': str(_('Мин. давление')), 'value': tv['pressure_min'], 'unit': str(_('бар')), 'type': 'number', 'order': 1},
                                {'key': 'pressure_max', 'label': str(_('Макс. давление')), 'value': tv['pressure_max'], 'unit': str(_('бар')), 'type': 'number', 'order': 2},
                                {'key': 'pressure_range', 'label': str(_('Диапазон')), 'value': tv['pressure_range'], 'unit': '', 'type': 'text', 'order': 3},
                            ]
                        },
                        {
                            'key': 'body',
                            'title': str(_('Корпус и материалы')),
                            'order': 4,
                            'fields': [
                                {'key': 'body_material', 'label': str(_('Материал корпуса')), 'value': tv['body_material'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'body_material_specified', 'label': str(_('Марка корпуса')), 'value': tv['body_material_specified'], 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'sealing_material_specified', 'label': str(_('Уплотнение')), 'value': tv['sealing_material_specified'], 'unit': '', 'type': 'text', 'order': 3},
                                {'key': 'solenoid_body_material', 'label': str(_('Материал соленоида')), 'value': tv['solenoid_body_material'], 'unit': '', 'type': 'text', 'order': 4},
                                {'key': 'solenoid_body_material_specified', 'label': str(_('Марка соленоида')), 'value': tv['solenoid_body_material_specified'], 'unit': '', 'type': 'text', 'order': 5},
                                {'key': 'weight', 'label': str(_('Вес')), 'value': tv['weight'], 'unit': str(_('кг')), 'type': 'number', 'order': 6},
                            ]
                        },
                        {
                            'key': 'connections',
                            'title': str(_('Присоединения')),
                            'order': 5,
                            'fields': [
                                {'key': 'pneumatic_connection', 'label': str(_('Пневмоприсоединение')), 'value': tv['pneumatic_connection'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'pneumatic_connection_thread', 'label': str(_('Резьба')), 'value': tv['pneumatic_connection_thread'], 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'cable_glands_holes', 'label': str(_('Отверстия КВ')), 'value': tv['cable_glands_holes'], 'unit': '', 'type': 'text', 'order': 3},
                            ]
                        },
                        {
                            'key': 'electric',
                            'title': str(_('Электрические параметры')),
                            'order': 6,
                            'fields': [
                                {'key': 'power_supply', 'label': str(_('Напряжение')), 'value': tv['power_supply'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'power_consumption_start', 'label': str(_('Мощность пусковая')), 'value': tv['power_consumption_start'], 'unit': str(_('Вт')), 'type': 'number', 'order': 2},
                                {'key': 'power_consumption_hot', 'label': str(_('Мощность номинальная')), 'value': tv['power_consumption_hot'], 'unit': str(_('Вт')), 'type': 'number', 'order': 3},
                                {'key': 'power_consumption_hold', 'label': str(_('Мощность удержания')), 'value': tv['power_consumption_hold'], 'unit': str(_('Вт')), 'type': 'number', 'order': 4},
                                {'key': 'solenoid_insulation_class', 'label': str(_('Класс изоляции')), 'value': tv['solenoid_insulation_class'], 'unit': '', 'type': 'text', 'order': 5},
                            ]
                        },
                        {
                            'key': 'protection',
                            'title': str(_('Защита')),
                            'order': 7,
                            'fields': [
                                {'key': 'ip', 'label': 'IP', 'value': tv['ip'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'exd', 'label': 'Ex', 'value': tv['exd'], 'unit': '', 'type': 'text', 'order': 2},
                            ]
                        },
                        {
                            'key': 'conditions',
                            'title': str(_('Условия эксплуатации')),
                            'order': 8,
                            'fields': [
                                {'key': 'temperature_range', 'label': str(_('Рабочая температура')), 'value': tv['temperature_range'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'medium_density_max', 'label': str(_('Макс. вязкость')), 'value': tv['medium_density_max'], 'unit': str(_('сСт')), 'type': 'number', 'order': 2},
                            ]
                        },
                    ]
                },
                {
                    'key': 'docs',
                    'title': str(_('Документация')),
                    'type': 'files',
                    'order': 3,
                    'data': self._get_docs_section(),
                },
                {
                    'key': 'certs',
                    'title': str(_('Сертификаты')),
                    'type': 'files',
                    'order': 4,
                    'data': self._get_certs_section(),
                },
                {
                    'key': 'description',
                    'title': str(_('Описание')),
                    'type': 'text',
                    'order': 5,
                    'data': self.description or '',
                },
            ],
        }

    def _get_model_line_summary(self) -> dict:
        if not self.model_line:
            return None
        return {
            'id': self.model_line.id,
            'name': self.model_line.name,
            'code': getattr(self.model_line, 'code', '') or '',
            'description': self.model_line.description or '',
            'construction': self.model_line.construction.name if self.model_line.construction else None,
            'operation': self.model_line.operation.name if self.model_line.operation else None,
            'brand': {
                'id': self.model_line.brand.id,
                'name': self.model_line.brand.name,
            } if self.model_line.brand else None,
        }

    def _get_sku_summary(self) -> dict:
        if not hasattr(self, 'sku') or not self.sku:
            return None
        return {
            'id': self.sku.id,
            'code': self.sku.code,
            'name': self.sku.name,
        }

    def to_values_dict(self) -> dict:
        """Облегчённая сериализация для списков."""
        first_img = self._get_first_image()
        tv = {'code': self.code or '', 'name': self.name or ''}
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title() or self.name or '',
            'image_alt': self._get_image_alt(),
            'template_vars': tv,
            'values': tv,
            'images': [first_img] if first_img else [],
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
        }

    def __str__(self):
        return self.name or ''

    def calculate_flow_rate(self, kv, p1_bar, p2_bar=None, medium='air', temp_c=20):
        """
        Расчет объемного расхода Q через коэффициент Kv.

        :param kv: Коэффициент пропускной способности (м3/ч)
        :param p1_bar: Давление на входе (абсолютное, бар)
        :param p2_bar: Давление на выходе (абсолютное, бар).
                       Если None, берем стандартный перепад для пневматики (p1-1)
        :param medium: 'air' (воздух) или 'water' (вода)
        :param temp_c: Температура среды (°C)
        :return: Расход Q (л/мин для воздуха, м3/ч для воды)
        Пример использования для воздуха (6 бар на входе, 5 на выходе):
            print(calculate_flow_rate(kv=0.5, p1_bar=6, medium='air'))
            Давление: В расчетах всегда используйте абсолютное давление (манометрическое + 1 бар), иначе при 0 бар на выходе (выхлоп в атмосферу) формула выдаст ошибку или 0.
            Для воздуха: Результат обычно выдается в Nl/min (нормальные литры в минуту). Именно это значение пишут в каталогах рядом с
            .
            Для воды: Результат обычно в м³/ч. Если нужны л/мин, просто умножьте на 16.67.
        """
        # Переводим в абсолютное давление (приблизительно +1 бар к манометрическому)
        # Если на входе 6 бар по манометру, то p1_abs = 7
        p1 = p1_bar + 1.013

        if p2_bar is None:
            p2 = p1 - 1.0  # Стандартный перепад в 1 бар для тестов
        else:
            p2 = p2_bar + 1.013

        delta_p = p1 - p2
        if delta_p <= 0:
            return 0

        if medium == 'water':
            # Формула для воды: Q = Kv * sqrt(delta_p)
            # Результат в м3/ч
            return kv * math.sqrt(delta_p)

        elif medium == 'air':
            # Упрощенная инженерная формула для воздуха (нормальные л/мин)
            # T_abs = Температура в Кельвинах
            t_abs = temp_c + 273.15

            # Проверка на критический перепад (p2 < 0.528 * p1)
            # Если перепад большой, расход "запирается" на скорости звука
            if p2 < 0.528 * p1:
                # Критическое течение
                q_nm3h = 243 * kv * p1 * math.sqrt(1 / t_abs)
            else:
                # Докритическое течение
                q_nm3h = 484 * kv * math.sqrt(delta_p * p2 / t_abs)

            # Перевод из м3/ч в л/мин: (Q * 1000) / 60
            return (q_nm3h * 1000) / 60