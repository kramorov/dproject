# pa_controls/models/limit_switch.py
import re
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Any

import logging

from core.models import TechDocMixin, ImageGalleryMixin
from core.models.catalog_mixin import CatalogFilterMixin, FilterFieldConfig, CommonFilterConfigs
from core.models.mixins import TemplateMixin, CopyMixin
from core.models.config_hash import ConfigHashMixin
from core.models.catalog_serializer import CatalogSerializerMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from core.utils.localization import localized_name, DEFAULT_LOCALE
from materials.models import MaterialGeneral, MaterialSpecified
from pa_controls.models.pa_control_options import LimitSwitchSensorVariety, SignalType, ContactForm, ContactState, PointsOption
from pa_controls.models.sensor import SensorComponent
from pa_controls.models.lsb_body import LimitSwitchBody
from pa_controls.models.lsb_model_line import LimitSwitchModelLine
from pa_controls.models.lsb_item_fields import (
    LSB_ITEM_TEMPLATE_FIELDS,
    LSB_NAME_FIELD_KEYS,
    LSB_VARS_FIELD_KEYS,
)
from params.exd_models import ExdOption
from options.models import ExdOptionsConsumerMixin
from sku.models import SKUMixin

# from pa_controls.models import PaControlMountingStandard

logger = logging.getLogger(__name__)

from params.models import IpOption


# ============================================================
# БЛОК КОНЦЕВЫХ ВЫКЛЮЧАТЕЛЕЙ (Limit Switch Box)
# ============================================================
class LimitSwitchBox(CatalogSerializerMixin,
                     ImageGalleryMixin,
                     TechDocMixin,
                     SmartCatalogMixin,
                     TemplateMixin,
                     SKUMixin, CopyMixin, ConfigHashMixin, ExdOptionsConsumerMixin, models.Model):
    """Модель блока концевых выключателей (каталог)
    points: int,
        1 точка - один датчик (обычно только на закрыто)
        2 точки - два датчика (на открыто и на закрыто) - самый распространенный вариант
        3 точки - три датчика (открыто, закрыто, промежуточное положение)
        4 точки - четыре датчика (два промежуточных положения + концевые)
    """
    exd_through_model = 'pa_controls.LimitSwitchExdOption'
    exd_m2m_field = 'exd'

    TEMPLATE_FIELDS = LSB_ITEM_TEMPLATE_FIELDS
    NAME_FIELD_KEYS = LSB_NAME_FIELD_KEYS
    VARS_FIELD_KEYS = LSB_VARS_FIELD_KEYS

    # SPEC_FIELD_KEYS закомментирован: спецификация задаётся spec_template.
    # SPEC_FIELD_KEYS = (
    #     'model_line_name', 'brand_name', 'sensor_variety', 'points', 'ip',
    #     'exd', 'work_temp', 'visual_indicator_type', 'body_material', 'weight',
    #     'cable_glands_holes', 'mounting', 'signals', 'sensors',
    # )

    # SPEC_GROUP_TITLES закомментирован: названия групп задаются в spec_template (JSON).
    # SPEC_GROUP_TITLES = {
    #     'general': 'Основные',
    #     'body': 'Корпус',
    #     'signals_feedback': 'Сигналы обратной связи',
    #     'sensors': 'Датчики',
    # }

    name = models.TextField(
        verbose_name=_("Название"),
        help_text=_('Текстовое название БКВ'))
    code = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey(LimitSwitchModelLine, related_name='limit_switch_box_model_line', blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия БКВ'),
                                   verbose_name=_("Серия"))
    body = models.ForeignKey(LimitSwitchBody, related_name='limit_switch_box_body', blank=True,
                             null=True,
                             on_delete=models.SET_NULL,
                             help_text=_('Корпус БКВ'),
                             verbose_name=_("Корпус"))
    # Характеристики
    sensor_variety = models.ForeignKey(
        LimitSwitchSensorVariety, on_delete=models.SET_NULL, null=True,
        help_text=_('Тип сенсора'),
        verbose_name=_("Тип сенсора")
    )

    primary_sensor = models.ForeignKey(
        SensorComponent,
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Датчик основной"),
        help_text=_("Основной датчик"),
        related_name='limit_switch_boxes_primary_sensor'  # обратная связь от датчика к корпусам
    )

    # Расширенный состав сигналов: роли → датчики (выходные сигналы БКВ)
    signal_profile = models.ForeignKey(
        'params.ControlUnitSignalProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='limit_switch_boxes',
        verbose_name=_("Профиль сигналов"),
        help_text=_("Расширенный состав сигналов БКВ: роль (Открыто/Закрыто/Промежуточное) → датчик")
    )

    points = models.IntegerField(default=2,
                                 verbose_name=_("Количество датчиков"),
                                 help_text=_("Количество точек переключения (датчиков)")
                                 )
    points_option = models.ForeignKey(
        PointsOption, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='limit_switch_boxes',
        verbose_name=_("Количество датчиков (опция)"),
        help_text=_("Ссылка на справочник количества датчиков")
    )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, null=True,
                           related_name='limit_switch_box_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    exd = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='+',
        help_text=_('Степень взрывозащиты (можно выбрать несколько вариантов)'),
        verbose_name=_("Взрывозащита")
    )
    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    # Материалы
    body_material = models.ForeignKey(MaterialGeneral, related_name='limit_switch_box_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    body_material_specified = models.ForeignKey(MaterialSpecified,
                                                related_name='limit_switch_box_body_material_specified',
                                                blank=True, null=True,
                                                on_delete=models.SET_NULL,
                                                help_text=_('Материал корпуса арматуры'),
                                                verbose_name=_('Материал корпуса'))

    # Дополнительные характеристики
    is_pneumatic = models.BooleanField(default=False, verbose_name=_("Пневматический"))
    has_namur_interface = models.BooleanField(default=False, verbose_name=_("NAMUR интерфейс"))
    visual_indicator_type = models.ForeignKey(
        'pa_controls.VisualIndicatorType',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='limit_switch_boxes',
        verbose_name=_("Вид визуального индикатора"),
        help_text=_("Вид купола-индикатора положения на корпусе БКВ")
    )

    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )
    # images заменён на image_gallery из ImageGalleryMixin
    # Переопределяем tech_docs из TechDocMixin
    tech_docs = models.ManyToManyField(
        'media_library.MediaLibraryItem',
        blank=True,
        related_name='+',
        verbose_name="Техдокументация",
    )

    class Meta:
        verbose_name = _("Блок концевых выключателей")
        verbose_name_plural = _("Блоки концевых выключателей")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — берётся из model_line."""
        return self.model_line.equipment_type

    def get_brand_for_sku(self):
        """Бренд для SKU — берётся из model_line."""
        return self.model_line.brand

    config_hash_fields = (
        'model_line', 'body', 'sensor_variety', 'primary_sensor', 'signal_profile',
        'points', 'points_option', 'ip', 'exd', 'work_temp_min', 'work_temp_max',
        'body_material', 'body_material_specified', 'is_pneumatic', 'has_namur_interface',
        'visual_indicator_type',
    )

    # ── Локализованное отображение (ru/en/cn) — денормализованный кэш для API/списков ──
    display_i18n = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Локализованное отображение (ru/en/cn)"),
        help_text=_('JSON: {"ru": {"name": ..., "description": ..., "title": ..., "list_title": ..., "spec_title": ...}, "en": {...}, "cn": {...}}. Обновляется при сохранении айтема и командой rebuild_display_i18n.')
    )

    def save(self, *args, **kwargs):
        """
        Сохраняет модель и синхронизирует номенклатуру (SKU).

        Вызывает ``sync_sku()`` после сохранения — создаёт новую SKU
        или «подхватывает» существующую по коду, обогащая её полями модели.
        """
        skip_display_i18n = kwargs.pop('skip_display_i18n', False)
        if not skip_display_i18n:
            # Фаза 4: денормализованный кэш локализованного отображения
            self.display_i18n = self.build_display_i18n()
        is_new = self.pk is None
        self.config_hash = self.compute_config_hash()
        self._check_config_hash_unique()
        super().save(*args, **kwargs)
        if is_new and self.model_line_id:
            self._sync_exd_options_from_model_line()
        self.sync_sku()

    def copy(self, suffix=' Копия', **kwargs):
        """Копия с гарантией уникальности кода и SKU.

        SKU привязывается по коду (sync_sku), поэтому повторные копии
        должны получать уникальный код: при конфликте перебираем
        «Копия 2», «Копия 3»… и подчищаем «сироту» от неудачной попытки.
        """
        from django.db import IntegrityError

        attempt = 0
        while True:
            s = suffix if attempt == 0 else f' Копия {attempt + 1}'
            try:
                return super().copy(suffix=s, **kwargs)
            except IntegrityError:
                attempt += 1
                if attempt > 100:
                    raise
                # Неудачная попытка могла оставить вставленную коробку без SKU
                LimitSwitchBox.objects.filter(
                    code=f"{self.code}{s}", sku__isnull=True
                ).delete()

    def _copy_custom_relations(self, new_copy):
        new_copy.exd.set(self.exd.all())

    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.model_line.description_template or None

    def _get_title_template_source(self):
        """Шаблон заголовка — из серии; fallback на EquipmentType (единый контракт)."""
        if not self.model_line:
            return None
        return getattr(self.model_line, 'title_template', None) or None

    @property
    def get_primary_sensor_contact_form(self) -> str:
        return '' if self.primary_sensor.contact_form.code == 'NONE' else self.primary_sensor.contact_form

    @staticmethod
    def _sensor_signal_marker(sensor, locale=None) -> str:
        """Маркер сигнала датчика: SPDT/DPDT/SPST или тип сигнала (аналоговый)."""
        if sensor.contact_form_id and sensor.contact_form.code != 'NONE':
            return sensor.contact_form.code
        if sensor.signal_type_id:
            return localized_name(sensor.signal_type, locale)
        return ''

    def get_signal_profile_summary(self, locale=None) -> str:
        """Текстовая сводка сигналов для описания (локализованная).

        Формат:
          Вых. Открыто — SPDT; Вых. Закрыто — SPDT; … Датчик: <код> - <характеристики>
        Маркер роли: код формы контактов (SPDT/DPDT/SPST), для аналоговых —
        тип сигнала. Характеристики датчика — как в поле «Доп. датчики».

        Без профиля — legacy-состав из primary_sensor (fallback).
        """
        locale = locale or DEFAULT_LOCALE
        sensor_prefix = {'ru': 'Датчик', 'en': 'Sensor', 'cn': '传感器'}.get(locale, 'Датчик')
        if self.signal_profile_id:
            entries = self.signal_profile.entries.select_related(
                'signal_role', 'sensor__signal_type', 'sensor__contact_form',
                'input_signal',
            ).all()
            parts = []
            sensors = []
            seen_sensors = set()
            for e in entries:
                if e.sensor_id:
                    marker = self._sensor_signal_marker(e.sensor, locale)
                    role = localized_name(e.signal_role, locale) if e.signal_role_id else '—'
                    if e.signal_role_id:
                        parts.append(f"{role} — {marker}" if marker else role)
                    if e.sensor.id not in seen_sensors:
                        seen_sensors.add(e.sensor.id)
                        sensors.append(e.sensor)
                elif e.input_signal_id:
                    if e.signal_role_id:
                        role = localized_name(e.signal_role, locale)
                        parts.append(f"{role} — {localized_name(e.input_signal, locale)}")
            for sensor in sensors:
                parts.append(f"{sensor_prefix}: {sensor.generate_name(locale)}")
            return "; ".join(parts) if parts else "—"

        # Fallback: старый состав (первичный датчик)
        parts = []
        if self.primary_sensor:
            component = self.primary_sensor.name
            if self.primary_sensor.signal_type_id:
                component += f" ({localized_name(self.primary_sensor.signal_type, locale)})"
            parts.append(component)
        return "; ".join(parts) if parts else "—"

    def get_signal_feedback_data(self, locale=None):
        """Два блока для карточки: сигналы обратной связи + уникальные датчики.

        Возвращает (signals, sensors):
          signals — список [(имя_роли, маркер)] по записям профиля;
          sensors — уникальные датчики без дублей, в порядке ролей.
        Без профиля — legacy: датчик из primary_sensor.
        """
        signals = []
        sensors = []
        if self.signal_profile_id:
            entries = self.signal_profile.entries.select_related(
                'signal_role', 'sensor__signal_type', 'sensor__contact_form',
                'input_signal',
            ).all()
            seen_sensors = set()
            for e in entries:
                if e.sensor_id:
                    signals.append((
                        localized_name(e.signal_role, locale) if e.signal_role_id else '—',
                        self._sensor_signal_marker(e.sensor, locale),
                    ))
                    if e.sensor.id not in seen_sensors:
                        seen_sensors.add(e.sensor.id)
                        sensors.append(e.sensor)
                elif e.input_signal_id:
                    signals.append((
                        localized_name(e.signal_role, locale) if e.signal_role_id else '—',
                        localized_name(e.input_signal, locale),
                    ))
        else:
            if self.primary_sensor:
                sensors.append(self.primary_sensor)
        return signals, sensors

    # FILTER_DEFINITIONS и QUICKSELECT_FILTERS вынесены в
    # pa_controls/catalog/filter_defs.py (единый источник с label_i18n).
    # Wizard/question_graph находят их через core/wizard_filter_registry.py.

    # ========== ОПЦИИ ДЛЯ ФИЛЬТРОВ (CUSTOM) ==========
    @classmethod
    def _get_exd_id_options(cls) -> List[Dict]:
        """Опции для фильтра Exd — все активные ExdOption"""
        return [
            {'id': obj.id, 'name': obj.name, 'code': obj.code}
            for obj in ExdOption.objects.filter(is_active=True).order_by('name')
        ]

    SEARCH_FIELDS = ['code', 'name', 'description']

    SELECT_RELATED_FIELDS = [
        'model_line', 'model_line__brand', 'sensor_variety',
        'image_gallery', 'model_line__image_gallery',
        'ip', 'body_material', 'primary_sensor', 'primary_sensor__signal_type', 'signal_profile', 'visual_indicator_type',
    ]

    # ========== СЕРИАЛИЗАЦИЯ (реестр) ==========

    # ── Вычисляемые display-значения (для реестра) ──

    @property
    def get_points_display(self) -> str:
        """Количество датчиков: название опции, иначе числовое значение."""
        if self.points_option:
            return self.points_option.name
        return str(self.points) if self.points else ''

    @property
    def get_work_temp_display(self) -> str:
        """Диапазон рабочей температуры для отображения."""
        if self.work_temp_min is None:
            return ''
        return f'{self.work_temp_min}...+{self.work_temp_max} °С'

    @property
    def get_weight_display(self) -> str:
        """Вес из корпуса."""
        body = self.body
        return str(body.weight) if body and body.weight else ''

    @property
    def get_is_pneumatic_display(self) -> str:
        return 'Да' if self.is_pneumatic else 'Нет'

    @property
    def get_has_namur_interface_display(self) -> str:
        return 'Да' if self.has_namur_interface else 'Нет'

    @property
    def get_cert_docs_description_display(self) -> str:
        """Описание сертификатов (property-обёртка над методом микса)."""
        return self.get_cert_docs_description() or ''

    # ── Структурированные значения (JSON/MCP) ──

    def get_signals_data(self, locale=None) -> list:
        """Сигналы обратной связи → список {name, marker}."""
        signals, _ = self.get_signal_feedback_data(locale=locale)
        return [{'name': name, 'marker': marker} for name, marker in signals]

    def get_sensors_data(self, locale=None) -> list:
        """Датчики → список {name}."""
        _, sensors = self.get_signal_feedback_data(locale=locale)
        return [{'name': sensor.generate_name(locale)} for sensor in sensors]