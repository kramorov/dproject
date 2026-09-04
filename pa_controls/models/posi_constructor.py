# pa_controls/models/posi_constructor.py
"""
Конструктор позиционеров (PositionerConstructor).

Паттерн — как у электроприводов (ea_actuator_constructor.py) и пневмоприводов
(pa_actuator_constructor.py):

    * Форма конструктора хранит ВЫБРАННЫЕ опции прямыми FK на реальные опции
      (или на through-строку, когда строка несёт дополнительные данные —
      температура, профиль сигналов со smart-набором, взрывозащита с M2M).
    * _OPTION_CONFIG — маппинг полей на through-модели уровня серии
      (через них проверяется доступность опции и берётся encoding).
    * Артикул/имя/описание генерирует ВРЕМЕННЫЙ PosiModelLineItem
      (build_preview_item) — единый источник истины, как в конструкторе ПП:
      item.generated_model_item_code + шаблоны названий серии.
    * save() = валидация → дефолты → синхронизация производных полей →
      генерация name/code/description → дедупликация.
    * Материализация в PosiModelLineItem + SKU выполняется сервисом
      pa_controls.services.posi_sku_service (аналог sku_service ПП):
      item.save() сам генерирует код и вызывает sync_sku().

В отличие от EA/PA здесь нет шага «модель серии» (model_line_item):
серия + набор опций и есть модель (PosiModelLineItem). Все опции —
уровня серии (parent_field='model_line').

Особенности позиционеров:
    * acting_type — не опция формы, а свойство серии (PosiModelLine.acting_type):
      тип выбирается ПЕРЕД серией как фильтр, на item переносится из серии.
    * Профиль сигналов — one и тот же профиль может повторяться в серии
      с разными наборами смарт-возможностей и encodings, поэтому форма
      хранит through-строку (selected_signal_profile_option), а реальный
      профиль и smart-набор синхронизируются из неё.
    * Взрывозащита — through-строка PosiExdOption хранит M2M видов Exd:
      форма хранит строку (selected_exd_row) + выбранный вид (selected_exd).
    * IP не участвует в конструкторе (у серий нет through-опции IP,
      позиционеру IP задаётся вручную в каталоге при необходимости).
"""
import logging
import re
from typing import Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .posi_model_line import (
    PosiModelLine,
    PosiBodyConnectionOption,
    PosiLeverOption,
    PosiTemperatureOption,
    PosiSignalProfileOption,
    PosiAlarmOption,
    PosiExdOption,
)
from .posi_options import LeverOption, SmartCapabilitySet
from .posi_body_connections import PosiBodyConnections
from .positioner_item import PosiModelLineItem

logger = logging.getLogger(__name__)


class PositionerConstructor(models.Model):
    """Сохранённая конфигурация конструктора позиционеров (форма).

    Результат работы конструктора — материализованный PosiModelLineItem + SKU
    (см. pa_controls.services.posi_sku_service). Форма нужна для хранения
    истории сборок, ленты «сохранённых конфигураций» и дедупликации.
    """

    # Шаг 2 конструктора: серия (после выбора типа действия)
    selected_model_line = models.ForeignKey(
        PosiModelLine,
        related_name='constructor_configs',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('Серия'),
        help_text=_('Серия позиционеров — фильтрует доступные опции'),
    )

    # ── Выбранные опции (прямые FK на реальные опции / through-строки) ──
    selected_body_connection = models.ForeignKey(
        PosiBodyConnections,
        related_name='posi_constructor_body_connections',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Присоединения корпуса'),
        help_text=_('Резьбы пневмовхода/выхода + отверстие под КВ'),
    )
    selected_lever = models.ForeignKey(
        LeverOption,
        related_name='posi_constructor_levers',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Рычаг'),
        help_text=_('Длина и тип рычага'),
    )
    # Температурное исполнение: through-модель САМА является опцией (как в ПП)
    selected_temperature = models.ForeignKey(
        PosiTemperatureOption,
        related_name='posi_constructor_temperatures',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Температурное исполнение'),
        help_text=_('Температурная through-опция серии'),
    )
    # Профиль сигналов: храним through-строку (один профиль может повторяться
    # с разными smart-наборами), реальный профиль — синхронизированное поле
    selected_signal_profile_option = models.ForeignKey(
        PosiSignalProfileOption,
        related_name='posi_constructor_signal_options',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Профиль сигналов (опция серии)'),
        help_text=_('Through-строка «Профиль сигналов» с encoding и smart-набором'),
    )
    selected_signal_profile = models.ForeignKey(
        'params.ControlUnitSignalProfile',
        related_name='posi_constructor_signal_profiles',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Профиль сигналов'),
        help_text=_('Реальный профиль сигналов (синхронизируется из опции серии)'),
    )
    selected_smart_capability_set = models.ForeignKey(
        SmartCapabilitySet,
        related_name='posi_constructor_smart_sets',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Набор смарт-возможностей'),
        help_text=_('Синхронизируется из выбранной through-строки профиля сигналов'),
    )
    selected_alarm = models.ForeignKey(
        'params.ControlUnitSignalProfile',
        related_name='posi_constructor_alarms',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Сигнал тревоги'),
        help_text=_('Профиль сигналов с ролью «Вых. Авария»'),
    )
    # Взрывозащита: строка-кодировка + выбранный вид Exd (M2M внутри строки)
    selected_exd_row = models.ForeignKey(
        PosiExdOption,
        related_name='posi_constructor_exd_rows',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Взрывозащита (кодировка)'),
        help_text=_('Through-строка PosiExdOption (кодировка + виды Exd)'),
    )
    selected_exd = models.ForeignKey(
        'params.ExdOption',
        related_name='posi_constructor_exd',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Вид взрывозащиты'),
        help_text=_('Выбранный вид Exd из M2M строки (пусто — общепром)'),
    )

    # Производные поля (синхронизируются в save(), как в EA/PA)
    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        verbose_name=_('Т мин, °С'),
        help_text=_('Минимальная рабочая температура, °С'),
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=80,
        verbose_name=_('Т макс, °С'),
        help_text=_('Максимальная рабочая температура, °С'),
    )

    name = models.CharField(max_length=300, blank=True, default='',
                            verbose_name=_('Название'))
    code = models.CharField(max_length=150, blank=True, null=True,
                            verbose_name=_('Артикул'))
    description = models.TextField(blank=True, default='',
                                   verbose_name=_('Описание'))
    sorting_order = models.IntegerField(default=0, verbose_name=_('Сортировка'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))
    is_unique = models.BooleanField(default=True,
                                    verbose_name=_('Уникальная конфигурация'))

    class Meta:
        ordering = ['sorting_order', 'id']
        verbose_name = _('Конфигурация конструктора позиционеров')
        verbose_name_plural = _('Конфигурации конструктора позиционеров')

    def __str__(self):
        return self.code or self.name or f'Конфигурация #{self.pk}'

    # ──────────────────────────────────────────────────────────────────
    # КОНФИГУРАЦИЯ ОПЦИЙ (паттерн EA/PA)
    # ──────────────────────────────────────────────────────────────────
    # through_attr = None → through-модель САМА является опцией
    # (temperature, signal_profile_option, exd_row).
    _OPTION_CONFIG = {
        'selected_body_connection': {
            'through_model_path': 'pa_controls.models.posi_model_line.PosiBodyConnectionOption',
            'through_attr': 'body_connection',
            'parent_field': 'model_line',
            'label': 'присоединения корпуса',
        },
        'selected_lever': {
            'through_model_path': 'pa_controls.models.posi_model_line.PosiLeverOption',
            'through_attr': 'lever',
            'parent_field': 'model_line',
            'label': 'рычаг',
        },
        'selected_temperature': {
            'through_model_path': 'pa_controls.models.posi_model_line.PosiTemperatureOption',
            'through_attr': None,
            'parent_field': 'model_line',
            'label': 'температурное исполнение',
        },
        'selected_signal_profile_option': {
            'through_model_path': 'pa_controls.models.posi_model_line.PosiSignalProfileOption',
            'through_attr': None,
            'parent_field': 'model_line',
            'label': 'профиль сигналов',
        },
        'selected_alarm': {
            'through_model_path': 'pa_controls.models.posi_model_line.PosiAlarmOption',
            'through_attr': 'alarm',
            'parent_field': 'model_line',
            'label': 'сигнал тревоги',
        },
        'selected_exd_row': {
            'through_model_path': 'pa_controls.models.posi_model_line.PosiExdOption',
            'through_attr': None,
            'parent_field': 'model_line',
            'label': 'взрывозащита',
        },
    }

    @classmethod
    def get_option_fields(cls) -> List[str]:
        """Список полей опций (для дедупликации и админки)."""
        return list(cls._OPTION_CONFIG.keys())

    @classmethod
    def _import_through_model(cls, config: dict):
        """Импорт through-модели по пути из конфига (паттерн EA/PA)."""
        import importlib
        module_name, class_name = config['through_model_path'].rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    @classmethod
    def _get_actual_option_from_through(cls, through_instance, config: dict):
        """Извлечь реальную опцию из through-строки (None → строка сама опция)."""
        through_attr = config.get('through_attr')
        if through_attr is None:
            return through_instance
        return getattr(through_instance, through_attr, None)

    def _get_parent_for_option(self, config: dict):
        """Родитель для всех опций позиционера — серия."""
        return self.selected_model_line

    # ──────────────────────────────────────────────────────────────────
    # ДОСТУПНЫЕ ОПЦИИ (для эндпоинта /options/)
    # ──────────────────────────────────────────────────────────────────

    def get_available_options(self) -> Dict[str, List[Dict]]:
        """Все доступные опции выбранной серии.

        Ключи словаря — группы опций (как в get_available_options у EA/PA):
            body_connections, levers, temperature_options,
            signal_profiles, alarms, exd_options.

        Каждая запись: id (through-строка), option_id (реальная опция),
        encoding, name, description, is_default, availability (где применимо).
        Для signal_profiles дополнительно smart_capability_set_id и capabilities.
        Для exd_options — variants (M2M видов Exd внутри кодировки).
        """
        result: Dict[str, List[Dict]] = {
            'body_connections': [],
            'levers': [],
            'temperature_options': [],
            'signal_profiles': [],
            'alarms': [],
            'exd_options': [],
        }
        ml = self.selected_model_line
        if not ml:
            return result

        for row in PosiBodyConnectionOption.objects.filter(
            model_line=ml, is_active=True
        ).select_related('body_connection'):
            result['body_connections'].append({
                'id': row.id,
                'option_id': row.body_connection_id,
                'encoding': row.encoding or '',
                'name': str(row.body_connection),
                'description': row.description or '',
                'is_default': row.is_default,
                'availability': row.exd_availability,
            })

        # Рычаги — только подходящие типу действия серии
        lever_qs = PosiLeverOption.objects.filter(
            model_line=ml, is_active=True
        ).select_related('lever', 'lever__acting_type')
        if ml.acting_type_id:
            lever_qs = lever_qs.filter(lever__acting_type_id=ml.acting_type_id)
        for row in lever_qs:
            result['levers'].append({
                'id': row.id,
                'option_id': row.lever_id,
                'encoding': row.encoding or '',
                'name': str(row.lever),
                'description': row.description or '',
                'is_default': row.is_default,
            })

        for row in PosiTemperatureOption.objects.filter(
            model_line=ml, is_active=True
        ):
            result['temperature_options'].append({
                'id': row.id,
                'option_id': row.id,  # through-модель сама опция
                'encoding': row.encoding or '',
                'name': f"{row.work_temp_min}...{row.work_temp_max} °С",
                'work_temp_min': row.work_temp_min,
                'work_temp_max': row.work_temp_max,
                'description': row.description or '',
                'is_default': row.is_default,
                'availability': row.exd_availability,
            })

        for row in PosiSignalProfileOption.objects.filter(
            model_line=ml, is_active=True
        ).select_related('signal_profile', 'smart_capability_set'):
            capabilities = []
            if row.smart_capability_set_id:
                capabilities = [c.name for c in row.smart_capability_set.get_capabilities()]
            result['signal_profiles'].append({
                'id': row.id,
                'option_id': row.signal_profile_id,
                'encoding': row.encoding or '',
                'name': row.name or str(row.signal_profile),
                'smart_capability_set_id': row.smart_capability_set_id,
                'capabilities': capabilities,
                'capabilities_display': '; '.join(capabilities),
                'description': row.description or '',
                'is_default': row.is_default,
                'availability': row.exd_availability,
            })

        for row in PosiAlarmOption.objects.filter(
            model_line=ml, is_active=True
        ).select_related('alarm'):
            result['alarms'].append({
                'id': row.id,
                'option_id': row.alarm_id,
                'encoding': row.encoding or '',
                'name': str(row.alarm),
                'description': row.description or '',
                'is_default': row.is_default,
            })

        for row in PosiExdOption.objects.filter(
            model_line=ml, is_active=True
        ).prefetch_related('exd_options'):
            variants = [
                {'option_id': v.id, 'name': v.name, 'code': v.code}
                for v in row.exd_options.all()
            ]
            if variants and all(not v['name'] for v in variants):
                variants = []  # пустой вид Exd («общепром») — не показываем вариантом
            name = ', '.join(v['name'] for v in variants) if variants else 'Общепром'
            result['exd_options'].append({
                'id': row.id,
                'encoding': row.encoding or '',
                'name': f"{row.encoding}: {name}" if row.encoding else name,
                'is_default': row.is_default,
                'variants': variants,
            })

        return result

    # ──────────────────────────────────────────────────────────────────
    # ВАЛИДАЦИЯ И ДЕФОЛТЫ (паттерн EA/PA)
    # ──────────────────────────────────────────────────────────────────

    def _ensure_valid_options(self):
        """Автозаполнение дефолтов + проверка валидности всех опций."""
        if not self.selected_model_line_id:
            return
        for field_name, config in self._OPTION_CONFIG.items():
            if not getattr(self, field_name):
                self._set_default_option(field_name, config)
        for field_name, config in self._OPTION_CONFIG.items():
            current_value = getattr(self, field_name)
            if current_value:
                self._validate_option(field_name, current_value, config)

    def _set_default_option(self, field_name, config):
        """Дефолтная through-строка (is_default=True, фолбэк — первая активная)."""
        try:
            ThroughModel = self._import_through_model(config)
            parent_obj = self._get_parent_for_option(config)
            if not parent_obj:
                return
            through_instance = ThroughModel.objects.filter(
                **{config['parent_field']: parent_obj, 'is_default': True, 'is_active': True}
            ).first()
            if not through_instance:
                through_instance = ThroughModel.objects.filter(
                    **{config['parent_field']: parent_obj, 'is_active': True}
                ).first()
            if through_instance:
                self._apply_through_instance(field_name, through_instance, config)
        except Exception as e:
            logger.error(f"Error setting default for {field_name}: {e}")

    def _apply_through_instance(self, field_name, through_instance, config):
        """Применить through-строку к полям формы.

        Для строки-опции (temperature / signal_profile_option / exd_row)
        синхронизирует производные поля (температуры, профиль+smart-набор,
        вид Exd).
        """
        if field_name == 'selected_temperature':
            self.selected_temperature = through_instance
            self.work_temp_min = through_instance.work_temp_min
            self.work_temp_max = through_instance.work_temp_max
        elif field_name == 'selected_signal_profile_option':
            self.selected_signal_profile_option = through_instance
            self.selected_signal_profile = through_instance.signal_profile
            self.selected_smart_capability_set = through_instance.smart_capability_set
        elif field_name == 'selected_exd_row':
            self.selected_exd_row = through_instance
            self.selected_exd = self._resolve_exd_variant(through_instance)
        else:
            actual_option = self._get_actual_option_from_through(through_instance, config)
            if actual_option:
                setattr(self, field_name, actual_option)

    @staticmethod
    def _resolve_exd_variant(exd_row) -> Optional['params.ExdOption']:
        """Первый вид Exd из M2M строки (или None для общепром)."""
        if not exd_row:
            return None
        variants = list(exd_row.exd_options.all())
        for variant in variants:
            if variant.code:  # запись с пустым code — заглушка «общепром»
                return variant
        return None

    def _validate_option(self, field_name, current_value, config):
        """Проверка, что опция разрешена для серии; невалидная — замена на дефолт."""
        try:
            ThroughModel = self._import_through_model(config)
            parent_obj = self._get_parent_for_option(config)
            if not parent_obj:
                return

            if field_name == 'selected_signal_profile_option':
                valid = ThroughModel.objects.filter(
                    id=current_value.id,
                    **{config['parent_field']: parent_obj, 'is_active': True}
                ).exists()
            elif field_name == 'selected_exd_row':
                valid = ThroughModel.objects.filter(
                    id=current_value.id,
                    **{config['parent_field']: parent_obj, 'is_active': True}
                ).exists()
            elif config.get('through_attr') is None:
                valid = ThroughModel.objects.filter(
                    id=current_value.id,
                    **{config['parent_field']: parent_obj, 'is_active': True}
                ).exists()
            else:
                through_attr = config['through_attr']
                valid = ThroughModel.objects.filter(
                    **{
                        f'{through_attr}_id': current_value.id,
                        config['parent_field']: parent_obj,
                        'is_active': True,
                    }
                ).exists()

            if not valid:
                default_through = ThroughModel.objects.filter(
                    **{config['parent_field']: parent_obj, 'is_default': True, 'is_active': True}
                ).first()
                if not default_through:
                    default_through = ThroughModel.objects.filter(
                        **{config['parent_field']: parent_obj, 'is_active': True}
                    ).first()
                if default_through:
                    self._apply_through_instance(field_name, default_through, config)
        except Exception as e:
            logger.error(f"Error validating {field_name}: {e}")

    # ──────────────────────────────────────────────────────────────────
    # СИНХРОНИЗАЦИЯ ПРОИЗВОДНЫХ ПОЛЕЙ
    # ──────────────────────────────────────────────────────────────────

    def _sync_derived_fields(self):
        """Синхронизировать температуры, профиль+smart-набор и вид Exd из строк."""
        if self.selected_temperature_id:
            self.work_temp_min = self.selected_temperature.work_temp_min
            self.work_temp_max = self.selected_temperature.work_temp_max
        if self.selected_signal_profile_option_id:
            row = self.selected_signal_profile_option
            self.selected_signal_profile = row.signal_profile
            self.selected_smart_capability_set = row.smart_capability_set
        if self.selected_exd_row_id:
            row = self.selected_exd_row
            if self.selected_exd_id and not row.exd_options.filter(
                pk=self.selected_exd_id
            ).exists():
                self.selected_exd = self._resolve_exd_variant(row)
            elif not self.selected_exd_id:
                self.selected_exd = self._resolve_exd_variant(row)

    # ──────────────────────────────────────────────────────────────────
    # ПРЕВЬЮ: ВРЕМЕННЫЙ ITEM (единый источник генерации кода)
    # ──────────────────────────────────────────────────────────────────

    def build_preview_item(self) -> Optional[PosiModelLineItem]:
        """Временный PosiModelLineItem из опций формы (без сохранения).

        Код/имя/описание генерирует именно item — так превью и сохранённый
        item гарантированно совпадают (паттерн ПП: preview = temp инстанс).
        """
        if not self.selected_model_line_id:
            return None
        item = PosiModelLineItem(
            model_line=self.selected_model_line,
            acting_type=self.selected_model_line.acting_type,
            body_connection=self.selected_body_connection,
            lever=self.selected_lever,
            work_temp_min=self.work_temp_min,
            work_temp_max=self.work_temp_max,
            signal_profile=self.selected_signal_profile,
            smart_capability_set=self.selected_smart_capability_set,
            alarm=self.selected_alarm,
        )
        # Взрывозащита в item теперь M2M (копируется из PosiExdOption серии),
        # а для артикула ({exd}) передаём выбранную through-строку.
        item._selected_exd_row = self.selected_exd_row
        item.code = item.generated_model_item_code
        item.name = item.generated_model_name_description('name') or ''
        item.description = item.generated_model_name_description('description') or ''
        return item

    @property
    def generated_model_item_code(self) -> str:
        item = self.build_preview_item()
        return item.generated_model_item_code if item else ''

    # Адаптер полей формы → encoding-свойства item (паттерн _get_option_encoding)
    _FIELD_TO_ITEM_ENCODING = {
        'selected_body_connection': 'body_connection_encoding',
        'selected_lever': 'lever_encoding',
        'selected_temperature': 'temperature_encoding',
        'selected_signal_profile': 'signal_profile_encoding',
        'selected_alarm': 'alarm_encoding',
        'selected_exd': 'exd_encoding',
    }

    def _get_option_encoding(self, field_name: str) -> str:
        """Encoding выбранной опции — через encoding-свойства item'а."""
        item = self.build_preview_item()
        if not item:
            return ''
        prop = self._FIELD_TO_ITEM_ENCODING.get(field_name)
        return getattr(item, prop, '') or '' if prop else ''

    # ──────────────────────────────────────────────────────────────────
    # ОПИСАНИЯ
    # ──────────────────────────────────────────────────────────────────

    def get_description_data(self) -> Dict[str, str]:
        """Плоский словарь данных для описаний и техописания."""
        item = self.build_preview_item()
        if not item:
            return {}
        tv = item.to_dict().get('template_vars', {})
        data = {
            'Серия': tv.get('model_line_name', ''),
            'Бренд': tv.get('brand_name', ''),
            'Тип действия': tv.get('acting_type', ''),
            'Взрывозащита': tv.get('exd', '') or 'Общепром',
            'Рабочая температура': tv.get('work_temp', ''),
            'Присоединения корпуса': tv.get('body_connection', ''),
            'Рычаг': tv.get('lever', ''),
            'Материал корпуса': tv.get('body_material', ''),
            'Вес': tv.get('weight', ''),
            'Давление питания': tv.get('supply_pressure', ''),
            'Пневмопривод': tv.get('actuator_action', ''),
            'Профиль сигналов': tv.get('signal_profile', ''),
            'Сигналы (по ролям)': tv.get('signal_profile_summary', ''),
            'Сигнал тревоги': tv.get('alarm', ''),
            'Сигнал тревоги (по ролям)': tv.get('alarm_signal_profile_summary', ''),
            'Смарт-возможности': tv.get('smart_capabilities', ''),
        }
        return {k: v for k, v in data.items() if v}

    def _generate_short_description(self) -> str:
        item = self.build_preview_item()
        return (item.name or '') if item else ''

    def _generate_tech_description(self) -> str:
        """Полное техописание (HTML-таблица) — для кнопки «Просмотр»."""
        data = self.get_description_data()
        rows = ''.join(
            f'<tr><td style="padding:4px 12px 4px 0;color:#666;white-space:nowrap;">{label}</td>'
            f'<td style="padding:4px 0;">{value}</td></tr>'
            for label, value in data.items()
        )
        return (
            '<div style="font-family:sans-serif;font-size:13px;">'
            f'<h3 style="margin:0 0 8px;">{self.generated_model_item_code}</h3>'
            f'<table style="border-collapse:collapse;">{rows}</table>'
            '</div>'
        )

    # ──────────────────────────────────────────────────────────────────
    # ДЕДУПЛИКАЦИЯ (паттерн EA/PA)
    # ──────────────────────────────────────────────────────────────────

    def _check_for_duplicates(self):
        """Поиск формы с тем же набором опций. Возвращает сообщение или None."""
        filters = {}
        for field_name in self.get_option_fields():
            field_value = getattr(self, field_name)
            if field_value:
                filters[field_name] = field_value
            else:
                filters[f'{field_name}__isnull'] = True
        # Производные поля, влияющие на состав конфигурации
        for extra in ('selected_signal_profile', 'selected_smart_capability_set', 'selected_exd'):
            field_value = getattr(self, extra)
            if field_value:
                filters[extra] = field_value
            else:
                filters[f'{extra}__isnull'] = True

        if self.selected_model_line:
            filters['selected_model_line'] = self.selected_model_line
        else:
            filters['selected_model_line__isnull'] = True

        duplicates = self.__class__.objects.filter(**filters)
        if self.pk:
            duplicates = duplicates.exclude(pk=self.pk)
        if duplicates.exists():
            duplicate = duplicates.first()
            return f"Найдена похожая конфигурация: {duplicate} (ID: {duplicate.id})"
        return None

    def _adjust_for_duplicate(self):
        """Суффикс (copy#XX) к name и code при дубликате (как в EA/PA)."""
        if not self.name:
            return
        from django.db.models import Q

        base_name = re.sub(r'\s*\(copy\s*#\d+\)$', '', self.name, flags=re.IGNORECASE).strip()
        existing = self.__class__.objects.filter(
            Q(name=self.name) |
            Q(name__iregex=r'^' + re.escape(base_name) + r'\s*\(copy\s*#\d+\)$')
        )
        max_number = 0
        for copy in existing:
            match = re.search(r'\(copy\s*#(\d+)\)$', copy.name, re.IGNORECASE)
            if match:
                max_number = max(max_number, int(match.group(1)))
            elif copy.name == self.name:
                max_number = max(max_number, 1)
        new_number = max_number + 1
        self.name = f"{self.name} (copy#{new_number:02d})"
        if self.code:
            clean_code = re.sub(r'\s*\(copy\s*#\d+\)$', '', self.code, flags=re.IGNORECASE)
            self.code = f"{clean_code} (copy#{new_number:02d})"

    # ──────────────────────────────────────────────────────────────────
    # SAVE (lifecycle, паттерн EA/PA)
    # ──────────────────────────────────────────────────────────────────

    def save(self, *args, **kwargs):
        self._ensure_valid_options()
        self._sync_derived_fields()

        item = self.build_preview_item()
        if item:
            self.name = item.name or ''
            self.code = item.code or None
            self.description = item.description or ''

        duplicate_message = self._check_for_duplicates()
        if duplicate_message:
            self.is_unique = False
            self._adjust_for_duplicate()
            logger.warning(f"Создается дубликат конфигурации: {duplicate_message}")
        else:
            self.is_unique = True

        super().save(*args, **kwargs)

    def clean(self):
        """Валидация комбинаций (делегирована item'у): рычаг/тип, «только общепром»."""
        item = self.build_preview_item()
        if not item:
            return
        errors = {}
        if (item.acting_type_id and item.lever_id
                and item.lever.acting_type_id
                and item.lever.acting_type_id != item.acting_type_id):
            errors['selected_lever'] = _('Рычаг не соответствует типу позиционера: '
                                         'для линейного нужен линейный рычаг, '
                                         'для ротационного — ротационный.')
        for conflict in item.get_ex_only_conflicts():
            field_map = {
                'signal_profile': 'selected_signal_profile',
                'body_connection': 'selected_body_connection',
                'work_temp_min': 'selected_temperature',
            }
            errors.setdefault(field_map.get(conflict['field'], conflict['field']),
                              conflict['message'])
        if errors:
            raise ValidationError(errors)
        super().clean()

    # ── Админка ──

    def description_preview(self):
        return (self.description or '')[:120]

    description_preview.short_description = _('Описание (превью)')
