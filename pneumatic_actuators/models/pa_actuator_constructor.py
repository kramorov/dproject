# pneumatic_actuators/models/pa_actuator_constructor.py

from django.db import models
from django.utils.translation import gettext_lazy as _

import importlib
from typing import List, Optional, Any, Dict
from decimal import Decimal
from django.core.exceptions import ValidationError
import re

import logging


logger = logging.getLogger(__name__)

from pneumatic_actuators.models import PneumaticActuatorModelLineItem, PneumaticCloseTimeParameter
from .py_options_constants import SAFETY_POSITION_NC_DEFAULT_CODE, ACTUATOR_VARIETY_RP_DEFAULT_CODE

class PneumaticActuatorConstructor(models.Model):
    """
    Конструктор пневмопривода — пошаговый выбор модели и опций через прямые FK.

    ## Архитектура
    В отличие от PneumaticActuatorSelected (through-модели M2M), здесь FK указывают
    напрямую на реальные опции (params.IpOption, params.ExdOption, ...).
    Доступность опций проверяется через through-модели из pa_options — они хранят
    связи «model_line → доступная опция» и «model_line_item → доступная опция».

    ## Поток работы
    1. Выбор серии (selected_model_line) → фильтруются model_line_items
    2. Выбор вида DA/SR → фильтруются model_line_items
    3. Выбор модели (selected_model_line_item) → загружаются доступные опции
    4. Опции автозаполняются дефолтами через through-модели
    5. save() генерирует name/code/description, проверяет дубликаты

    ## Генерация кода
    encoding для кода берётся из through-моделей (не code реальных опций!).
    _get_option_encoding() находит through-запись по ID опции + родителю.
    Шаблон артикула — model_line.model_item_code_template.

    ## API
    - ConstructorViewSet: CRUD + model_lines + model_line_items + options + preview
    - /preview/ — генерирует код и описание без сохранения в базу
    - /{id}/options/ — список доступных опций для выбранной модели
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
        'PneumaticActuatorModelLine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='constructor_model_lines',
        verbose_name=_('Серия'),
        help_text=_('Серия пневмоприводов — фильтрует доступные модели')
    )

    # Шаг 2: выбор конкретной модели (model_line_item) — фильтруется по selected_model_line
    selected_model_line_item = models.ForeignKey(
        PneumaticActuatorModelLineItem,
        related_name='constructor_model_line_items',
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_('Модель'),
        help_text=_('Модель пневмопривода'))

    # Выбранные опции — прямые FK на реальные опции (не through-модели)
    selected_safety_position = models.ForeignKey(
        'params.SafetyPositionOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Выбранное положение безопасности"),
        help_text=_('Выбранное положение безопасности привода')
    )

    selected_springs_qty = models.ForeignKey(
        'pneumatic_actuators.PneumaticActuatorSpringsQty',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Выбранное количество пружин"),
        help_text=_('Выбранное количество пружин привода')
    )

    # Температурная опция — PneumaticTemperatureOption сама является опцией
    # (нет отдельной params.TemperatureOption, данные t° хранятся в through-модели)
    selected_temperature = models.ForeignKey(
        'PneumaticTemperatureOption',
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

    selected_hand_wheel = models.ForeignKey(
        'params.HandWheelInstalledOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Встроенный дублер"),
        help_text=_('Встроенный ручной дублер')
    )
    is_unique = models.BooleanField(default=True, verbose_name='Это уникальная конфигурация')

    # ОБЩАЯ КОНФИГУРАЦИЯ ДЛЯ ВСЕХ ВАЛИДАЦИЙ
    # through_model_path — путь к through-модели для проверки доступности
    # through_attr — имя атрибута through-модели, указывающего на реальную опцию (None = through-модель сама опция)
    _OPTION_CONFIG = {
        'selected_safety_position': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticSafetyPositionOption',
            'through_attr': 'safety_position',
            'label': 'положение безопасности',
            'parent_field': 'model_line_item',
        },
        'selected_springs_qty': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticSpringsQtyOption',
            'through_attr': 'springs_qty',
            'label': 'количество пружин',
            'parent_field': 'model_line_item',
        },
        'selected_temperature': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticTemperatureOption',
            'through_attr': None,  # PneumaticTemperatureOption САМА является опцией
            'label': 'температурная опция',
            'parent_field': 'model_line',
        },
        'selected_ip': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticIpOption',
            'through_attr': 'ip_option',
            'label': 'степень защиты IP',
            'parent_field': 'model_line',
        },
        'selected_exd': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticExdOption',
            'through_attr': 'exd_option',
            'label': 'взрывозащита',
            'parent_field': 'model_line',
        },
        'selected_body_coating': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticBodyCoatingOption',
            'through_attr': 'body_coating_option',
            'label': 'покрытие корпуса',
            'parent_field': 'model_line',
        },
        'selected_hand_wheel': {
            'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticHandWheelOption',
            'through_attr': 'hand_wheel_option',
            'label': 'ручной дублер',
            'parent_field': 'model_line',
        }
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
        Если through_attr is None — through-модель сама является опцией (temperature).
        """
        through_attr = config.get('through_attr')
        if through_attr is None:
            return through_instance  # PneumaticTemperatureOption сама опция
        return getattr(through_instance, through_attr, None)

    @classmethod
    def get_for_select(cls, model_line_id: Optional[int] = None,
                       model_line_item_id: Optional[int] = None,
                       active_only: bool = True) -> List[Dict]:
        """
        Получить список сконструированных приводов для выпадающего списка.
        Фильтруется по серии и/или модели.
        """
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
        verbose_name = _('Конструктор пневмопривода')
        verbose_name_plural = _('Конструктор пневмоприводов')

    def __str__(self):
        return self.name

    # ==================== Вспомогательные методы ====================

    def _generate_tech_description_for_display(self) -> str:
        """Обёртка для совместимости: возвращает техническое описание."""
        return self._generate_tech_description()

    def _generate_html_description(self) -> str:
        """Генерация HTML-описания привода для rich-отображения."""
        desc_parts = []
        if self.description:
            desc_parts.append(f'<p>{self.description}</p>')
        if self.selected_model_line_item and self.selected_model_line_item.description:
            desc_parts.append(f'<p><strong>Описание модели:</strong> {self.selected_model_line_item.description}</p>')
        result = '<br>'.join(desc_parts)
        # Отладка: показываем фрагмент вокруг таблицы
        # idx = result.find('<table')
        # if idx >= 0:
        #     print(f"TECH_DESC_FINAL (around table): ...{result[max(0,idx-100):idx+200]}...")
        # else:
        #     print(f"TECH_DESC_FINAL (no table): {result[-300:]}")
        return result

    def get_description_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Унифицированная плоская структура данных для описания сконструированного привода.
        Использует прямые FK (не through-модели) — в отличие от PneumaticActuatorSelected.
        """
        import traceback
        logger.debug("get_description_data")

        data = {}
        item = self.selected_model_line_item
        if not item:
            return data

        # ==================== MAIN ====================
        model_display = self.code or (item.code if item else None) or 'Не указано'
        data['model_name'] = {
            'category': 'main',
            'title': 'Модель',
            'data': self.code or item.code if item else None,
            'display_data': model_display,
            'text_data': f"Модель: {model_display}" if model_display != 'Не указано' else None,
            'name': model_display if model_display != 'Не указано' else '',
        }

        # ==================== BASIC PROPERTIES ====================
        model_line = item.model_line
        data['brand'] = {
            'category': 'basic_properties',
            'title': 'Бренд',
            'data': model_line.brand_id if model_line and model_line.brand else None,
            'display_data': model_line.brand.name if model_line and model_line.brand else 'Не указано',
            'text_data': f"Бренд: {model_line.brand.name}" if model_line and model_line.brand else None,
            'name': model_line.brand.name if model_line and model_line.brand else '',
        }

        _VARIETY_LABELS = {'DA': 'Двойного действия', 'SR': 'Одностороннего действия с возвратной пружиной'}
        actuator_variety = item.pneumatic_actuator_variety
        data['pneumatic_actuator_variety'] = {
            'category': 'basic_properties',
            'title': 'Вид привода (DA/SR)',
            'data': actuator_variety.id if actuator_variety else None,
            'display_data': actuator_variety.name if actuator_variety else 'Не указано',
            'text_data': f"Вид привода: {actuator_variety.name}" if actuator_variety else None,
            'code': actuator_variety.code if actuator_variety else '',
            'name': actuator_variety.name if actuator_variety else '',
            'description': _VARIETY_LABELS.get(actuator_variety.code, actuator_variety.name) if actuator_variety else '',
        }

        data['output_type'] = {
            'category': 'basic_properties',
            'title': 'Тип работы',
            'display_data': 'Четвертьоборотный',
        }

        construction_variety = item.pneumatic_actuator_construction_variety
        data['construction_variety'] = {
            'category': 'basic_properties',
            'title': 'Конструкция',
            'data': construction_variety.id if construction_variety else None,
            'display_data': construction_variety.name if construction_variety else 'Не указано',
            'code': construction_variety.code if construction_variety else '',
            'name': construction_variety.name if construction_variety else '',
        }

        # ==================== BODY SPECS — через тело привода ====================
        try:
            if item.body:
                body_data = item.body.get_description_data()
                for key, value in body_data.items():
                    data[f'body_{key}'] = value
                logger.debug(f"body_data added, keys: {list(body_data.keys())}")
        except Exception as e:
            logger.error(f"Error adding body_data: {e}")
            traceback.print_exc()

        # ==================== SELECTED OPTIONS — прямые FK ====================
        # safety_position → params.SafetyPositionOption
        _SAFETY_LABELS = {'NC': 'Нормально закрытое (НЗ)', 'NO': 'Нормально открытое (НО)'}
        sp = self.selected_safety_position
        data['safety_position'] = {
            'category': 'selected_options',
            'title': 'Положение безопасности',
            'data': sp.id if sp else None,
            'display_data': sp.name if sp else 'Не указано',
            'text_data': f"Положение безопасности: {sp.name}" if sp else None,
            'code': sp.code if sp else '',
            'name': sp.name if sp else '',
            'description': _SAFETY_LABELS.get(sp.code, sp.name) if sp else '',
        }

        # springs_qty → pneumatic_actuators.PneumaticActuatorSpringsQty (прямой FK)
        sq = self.selected_springs_qty
        data['springs_qty'] = {
            'category': 'selected_options',
            'title': 'Количество пружин',
            'data': sq.id if sq else None,
            'display_data': sq.name if sq else 'Не указано',
            'text_data': f"Количество пружин: {sq.name}" if sq else None,
            'code': sq.code if sq else '',
            'name': sq.name if sq else '',
        }

        # temperature → PneumaticTemperatureOption (through-модель = сама опция)
        st = self.selected_temperature
        data['temperature'] = {
            'category': 'selected_options',
            'title': 'Температурное исполнение',
            'data': st.id if st else None,
            'display_data': str(st) if st else 'Не указано',
            'text_data': f"Температурное исполнение: {st}" if st else None,
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
            'text_data': f"IP защита: {ip.name}" if ip else None,
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
            'text_data': f"Взрывозащита: {ex.name}" if ex else None,
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
            'text_data': f"Покрытие корпуса: {bc.name}" if bc else None,
            'code': bc.code if bc else '',
            'name': bc.name if bc else '',
        }

        # hand_wheel → params.HandWheelInstalledOption
        hw = self.selected_hand_wheel
        data['hand_wheel'] = {
            'category': 'selected_options',
            'title': 'Ручной дублер',
            'data': hw.id if hw else None,
            'display_data': hw.name if hw else 'Не указано',
            'text_data': f"Ручной дублер: {hw.name}" if hw else None,
            'code': hw.code if hw else '',
            'name': hw.name if hw else '',
        }

        # ==================== CALCULATED PARAMETERS ====================
        try:
            ttc_result = PneumaticCloseTimeParameter.get_time_to_close(
                item.body_id,
                self.selected_springs_qty,
                pressure=None
            )
        except Exception:
            ttc_result = None

        # get_time_to_close возвращает dict {time_open, time_close, ...} или None
        ttc_close = ttc_result.get('time_close') if isinstance(ttc_result, dict) else None
        ttc_open = ttc_result.get('time_open') if isinstance(ttc_result, dict) else None
        print(f"TTC: result={ttc_result}, close={ttc_close}, open={ttc_open}")

        weight_val = self.calculated_weight
        data['weight'] = {
            'category': 'calculated',
            'title': 'Вес',
            'data': float(weight_val) if weight_val is not None else None,
            'display_data': f"{float(weight_val):.1f} кг" if weight_val is not None else 'Не указано',
            'text_data': f"Вес: {float(weight_val):.1f} кг" if weight_val is not None else None,
            'value': float(weight_val) if weight_val is not None else None,
        }
        data['time_to_close'] = {
            'category': 'calculated',
            'title': 'Время закрытия',
            'data': ttc_close,
            'display_data': f"{ttc_close:.1f} сек" if ttc_close is not None else 'Не указано',
            'text_data': f"Время закрытия: {ttc_close:.1f} сек" if ttc_close is not None else None,
            'value': ttc_close,
        }
        data['time_to_open'] = {
            'category': 'calculated',
            'title': 'Время открытия',
            'data': ttc_open,
            'display_data': f"{ttc_open:.1f} сек" if ttc_open is not None else 'Не указано',
            'text_data': f"Время открытия: {ttc_open:.1f} сек" if ttc_open is not None else None,
            'value': ttc_open,
        }

        # ==================== TORQUE / THRUST TABLE ====================
        try:
            spring_qty = self.selected_springs_qty  # прямой FK на PneumaticActuatorSpringsQty
            ncno_code = sp.code if sp else SAFETY_POSITION_NC_DEFAULT_CODE
            construction_variety_code = construction_variety.code if construction_variety else ACTUATOR_VARIETY_RP_DEFAULT_CODE
            da_sr_code = actuator_variety.code if actuator_variety else None

            print(f"TORQUE: body={item.body}, body_id={item.body_id}, spring_qty={spring_qty}, "
                        f"ncno={ncno_code}, constr={construction_variety_code}, da_sr={da_sr_code}")
            logger.info(f"TORQUE: body={item.body}, body_id={item.body_id}, spring_qty={spring_qty}, "
                        f"ncno={ncno_code}, constr={construction_variety_code}, da_sr={da_sr_code}")

            from pneumatic_actuators.models import BodyThrustTorqueTable
            torque_data = BodyThrustTorqueTable.get_torque_thrust_values(
                current_body=item.body,
                spring_qty_list=[spring_qty] if spring_qty else None,
                ncno_code=ncno_code,
                construction_variety_code=construction_variety_code,
                da_sr_code=da_sr_code,
            )
            print(f"TORQUE_RESULT: type={type(torque_data)}, keys={list(torque_data.keys()) if isinstance(torque_data, dict) else 'N/A'}")
            logger.info(f"TORQUE: torque_data type={type(torque_data)}, keys={list(torque_data.keys()) if isinstance(torque_data, dict) else 'N/A'}")
            if isinstance(torque_data, dict):
                td_data = torque_data.get('data')
                logger.info(f"TORQUE: inner data type={type(td_data)}, "
                            f"by_spring keys={list(td_data.get('by_spring', {}).keys()) if isinstance(td_data, dict) else 'N/A'}")
            # Санитизация: убираем несериализуемые поля (format — builtin в ответе об ошибке)
            if isinstance(torque_data, dict):
                torque_data.pop('format', None)
                if isinstance(torque_data.get('data'), list):
                    torque_data = None  # ошибка — data = [], не показываем
            data['torque_thrust_table'] = {
                'category': 'torque',
                'title': 'Таблица моментов/усилий',
                'data': torque_data,
                'display_data': 'Данные доступны' if torque_data else 'Не указано',
                'text_data': None,
            }
        except Exception as e:
            logger.error(f"Error getting torque/thrust table: {e}")
            traceback.print_exc()
            data['torque_thrust_table'] = {
                'category': 'torque',
                'title': 'Таблица моментов/усилий',
                'data': None,
                'display_data': 'Ошибка загрузки',
                'text_data': None,
            }

        return data

    def _generate_short_description(self) -> str:
        """
        Генерирует краткое описание привода для поля description.
        Формат: «{code}-Тип: четвертьоборотный пневмопривод ...; Положение безопасности: ...; ...»
        Используется при подстановке в КП в название номенклатуры.
        """
        data = self.get_description_data()
        desc_parts = []

        model_name = data.get('model_name', {}).get('display_data', '')
        if not model_name or model_name == 'Не указано':
            return "Модель: не выбрана"

        short_description = f"{model_name}-"

        # Базовые свойства
        variety_code = data.get('pneumatic_actuator_variety', {}).get('code', '')
        short_description += f"Тип: четвертьоборотный пневмопривод"
        if variety_code == 'SR':
            springs_display = data.get('springs_qty', {}).get('display_data', '')
            short_description += f" с возвратной пружиной, кол-во пружин {springs_display};"
        else:
            short_description += f" двойного действия;"

        # Выбранные опции
        safety = data.get('safety_position', {}).get('display_data', '')
        short_description += f" Положение безопасности: {safety};"

        temp = data.get('temperature', {}).get('display_data', '')
        short_description += f" Темп.исп. {temp};"

        ip = data.get('ip', {}).get('display_data', '')
        short_description += f" {ip};"

        exd = data.get('exd', {}).get('display_data', '')
        short_description += f" {exd};"

        coating = data.get('body_coating', {}).get('display_data', '')
        short_description += f" Покрытие корпуса: {coating};"

        hand_wheel = data.get('hand_wheel', {}).get('display_data', '')
        short_description += f" Ручной дублер на корпусе:{hand_wheel};"

        return short_description

    def _generate_tech_description(self) -> str:
        """
        Генерирует полное техническое описание привода (как в админке Selected).
        Включает: модель, бренд, тип привода, тип работы, конструкцию,
        все опции, характеристики корпуса, шток, подключения, вес, таблицу моментов.
        """
        data = self.get_description_data()
        desc_parts = []

        # ==================== ЗАГОЛОВОК ====================
        code = self.code or self.generated_model_item_code or data.get('model_name', {}).get('display_data', '')
        desc_parts.append(f"Описание пневмопривода<br>Код: {code}<br>")

        # ==================== МОДЕЛЬ ====================
        model_name = data.get('model_name', {}).get('display_data')
        if model_name and model_name != 'Не указано':
            desc_parts.append(f"Модель: {model_name}")
        else:
            desc_parts.append("Модель: не выбрана")

        # ==================== БАЗОВЫЕ СВОЙСТВА ====================
        brand = data.get('brand', {}).get('display_data')
        if brand and brand != 'Не указано':
            desc_parts.append(f"Бренд: {brand}")

        actuator_variety = data.get('pneumatic_actuator_variety', {}).get('display_data')
        if actuator_variety and actuator_variety != 'Не указано':
            desc_parts.append(f"Тип привода: {actuator_variety}")

        output_type = data.get('output_type', {}).get('display_data')
        if output_type and output_type != 'Не указано':
            desc_parts.append(f"Тип работы: {output_type}")

        construction_variety = data.get('construction_variety', {}).get('display_data')
        if construction_variety and construction_variety != 'Не указано':
            desc_parts.append(f"Тип конструкции: {construction_variety}")

        # ==================== ВЫБРАННЫЕ ОПЦИИ ====================
        selected_options = []

        safety = data.get('safety_position', {}).get('display_data')
        if safety and safety != 'Не указано':
            selected_options.append(f"Положение безопасности: {safety}")

        springs = data.get('springs_qty', {}).get('display_data')
        if springs and springs != 'Не указано':
            selected_options.append(f"Количество пружин: {springs}")

        temperature = data.get('temperature', {}).get('display_data')
        if temperature and temperature != 'Не указано':
            selected_options.append(f"Температурный диапазон: {temperature}")

        ip = data.get('ip', {}).get('display_data')
        if ip and ip != 'Не указано':
            selected_options.append(f"Степень защиты IP: {ip}")

        exd = data.get('exd', {}).get('display_data')
        if exd and exd != 'Не указано':
            selected_options.append(f"Взрывозащита: {exd}")

        coating = data.get('body_coating', {}).get('display_data')
        if coating and coating != 'Не указано':
            selected_options.append(f"Покрытие корпуса: {coating}")

        hand_wheel = data.get('hand_wheel', {}).get('display_data')
        if hand_wheel and hand_wheel != 'Не указано':
            selected_options.append(f"Ручной дублер: {hand_wheel}")

        if selected_options:
            desc_parts.append("Выбранные опции:")
            desc_parts.extend(f"  {opt}" for opt in selected_options)

        # ==================== ХАРАКТЕРИСТИКИ КОРПУСА ====================
        body_specs = []

        piston = data.get('body_piston_diameter', {}).get('display_data')
        if piston and piston != 'Не указано':
            body_specs.append(f"Диаметр поршня: {piston}")

        turn_angle = data.get('body_turn_angle', {}).get('display_data')
        if turn_angle and turn_angle != 'Не указано':
            body_specs.append(f"Угол поворота: {turn_angle}")

        turn_limit = data.get('body_turn_tuning_limit', {}).get('display_data')
        if turn_limit and turn_limit != 'Не указано':
            body_specs.append(f"Ограничитель поворота: {turn_limit}")

        weight_spring = data.get('body_weight_spring', {}).get('display_data')
        if weight_spring and weight_spring != 'Не указано':
            body_specs.append(f"Вес пружины: {weight_spring}")

        min_pressure = data.get('body_min_pressure', {}).get('display_data')
        max_pressure = data.get('body_max_pressure', {}).get('display_data')
        if min_pressure or max_pressure:
            body_specs.append(f"Давление: {min_pressure or '—'} / {max_pressure or '—'}")

        air_open = data.get('body_air_usage_open', {}).get('display_data')
        air_close = data.get('body_air_usage_close', {}).get('display_data')
        if air_open or air_close:
            body_specs.append(f"Расход воздуха: открытие {air_open or '—'}, закрытие {air_close or '—'}")

        if body_specs:
            desc_parts.append("Характеристики корпуса:")
            desc_parts.extend(f"  {spec}" for spec in body_specs)

        # ==================== ИНФОРМАЦИЯ О ШТОКЕ ====================
        stem_parts = []
        stem_shape = data.get('body_stem_shape', {}).get('display_data')
        if stem_shape and stem_shape != 'Не указано':
            stem_parts.append(f"форма: {stem_shape}")

        stem_size = data.get('body_stem_size', {}).get('display_data')
        if stem_size and stem_size != 'Не указано':
            stem_parts.append(f"размер: {stem_size}")

        stem_height = data.get('body_max_stem_height', {}).get('display_data')
        if stem_height and stem_height != 'Не указано':
            stem_parts.append(f"макс. высота: {stem_height}")

        stem_diameter = data.get('body_max_stem_diameter', {}).get('display_data')
        if stem_diameter and stem_diameter != 'Не указано':
            stem_parts.append(f"макс. диаметр: {stem_diameter}")

        if stem_parts:
            desc_parts.append("Присоединение к арматуре:")
            desc_parts.append(f"  Шток: {', '.join(stem_parts)}")

        mounting_plates = data.get('body_mounting_plates', {}).get('display_data')
        if mounting_plates and mounting_plates != 'Не указано':
            desc_parts.append(f"  Монтажные площадки: {mounting_plates}")

        # ==================== ПОДКЛЮЧЕНИЯ ====================
        connections = []
        thread_in = data.get('body_thread_in', {}).get('display_data')
        if thread_in and thread_in != 'Не указано':
            connections.append(f"Пневмовход: {thread_in}")

        thread_out = data.get('body_thread_out', {}).get('display_data')
        if thread_out and thread_out != 'Не указано':
            connections.append(f"Пневмовыход: {thread_out}")

        pneum_conn = data.get('body_pneumatic_connections', {}).get('display_data')
        if pneum_conn and pneum_conn != 'Не указано':
            connections.append(f"Типы пневмоподключений: {pneum_conn}")

        if connections:
            desc_parts.append("Подключения корпуса:")
            desc_parts.extend(f"  {conn}" for conn in connections)

        # ==================== ВЕС И ВРЕМЯ ====================
        weight = data.get('weight', {}).get('display_data')
        if weight and weight != 'Не указано':
            desc_parts.append(f"Вес: {weight}")

        ttc = data.get('time_to_close', {}).get('display_data')
        if ttc and ttc != 'Не указано':
            desc_parts.append(f"Время закрытия: {ttc}")

        tto = data.get('time_to_open', {}).get('display_data')
        if tto and tto != 'Не указано':
            desc_parts.append(f"Время открытия: {tto}")

        # ==================== ТАБЛИЦА МОМЕНТОВ/УСИЛИЙ ====================
        torque_table = data.get('torque_thrust_table', {})
        table_data = torque_table.get('data')

        print(f"TECH_DESC: torque_table keys={list(torque_table.keys())}, "
                    f"table_data type={type(table_data)}, "
                    f"table_data is dict={isinstance(table_data, dict)}, "
                    f"inner data type={type(table_data.get('data')) if isinstance(table_data, dict) else 'N/A'}")
        logger.info(f"TECH_DESC: torque_table keys={list(torque_table.keys())}, "
                    f"table_data type={type(table_data)}, "
                    f"table_data is dict={isinstance(table_data, dict)}, "
                    f"inner data type={type(table_data.get('data')) if isinstance(table_data, dict) else 'N/A'}")

        if table_data and isinstance(table_data, dict) and isinstance(table_data.get('data'), dict):
            table_config = table_data.get('table_config', {})
            data_by_spring = table_data.get('data', {}).get('by_spring', {})

            if data_by_spring:
                visible_fields = table_config.get('visible_fields', [])
                pressure_order = table_config.get('pressure_order', [])
                spring_order = table_config.get('spring_order', [])
                torque_format = table_config.get('format', {}).get('torque', {})

                heading = 'Таблица моментов:' if 'torque' in (table_config.get('type') or '') else 'Таблица моментов/усилий:'
                # Собираем всю таблицу в одну строку — без разбивки на элементы массива
                table_parts = [f'{heading}<table border="1" style="border-collapse: collapse; margin: 4px 0; width: 100%;">']
                table_parts.append('<thead>')
                table_parts.append('<tr><th rowspan="2">Пружины</th>')

                for pressure_code in pressure_order:
                    col_span = len(visible_fields)
                    table_parts.append(f'<th colspan="{col_span}">{pressure_code}</th>')
                table_parts.append('</tr>')

                table_parts.append('<tr>')
                for _ in pressure_order:
                    for field in visible_fields:
                        table_parts.append(f'<th>{field.upper()}</th>')
                table_parts.append('</tr>')
                table_parts.append('</thead>')

                table_parts.append('<tbody>')
                for spring_code in spring_order:
                    if spring_code in data_by_spring:
                        table_parts.append(f'<tr><td>{spring_code}</td>')
                        spring_data = data_by_spring[spring_code]
                        pressures_data = spring_data.get('pressures', {})

                        for pressure_code in pressure_order:
                            if pressure_code in pressures_data:
                                pressure_values = pressures_data[pressure_code]
                                for field in visible_fields:
                                    value = pressure_values.get(field)
                                    if value is not None:
                                        precision = torque_format.get('precision', 1)
                                        table_parts.append(f'<td>{value:.{precision}f}</td>')
                                    else:
                                        table_parts.append('<td>—</td>')
                            else:
                                for _ in visible_fields:
                                    table_parts.append('<td>—</td>')
                        table_parts.append('</tr>')
                table_parts.append('</tbody>')
                table_parts.append('</table>')
                desc_parts.append(''.join(table_parts))

                desc_parts.append(f"Примечание: значения в {torque_format.get('unit', 'Нм')}")

        result = '<br>'.join(desc_parts)
        # Отладка: показываем фрагмент вокруг таблицы
        idx = result.find('<table')
        if idx >= 0:
            print(f"TECH_DESC_FINAL (around table): ...{result[max(0,idx-100):idx+200]}...")
        else:
            print(f"TECH_DESC_FINAL (no table): {result[-300:]}")
        return result

    def get_structured_data(self) -> Dict[str, Any]:
        """
        Структурированные данные для API-ответа.
        Возвращает словарь с ключами: model, basic_properties, selected_options,
        calculated_parameters, torque_thrust_table, formatted (short/technical/html).
        """
        data = self.get_description_data()
        structured_data = {
            'model': {
                'name': data.get('model_name', {}).get('display_data'),
                'code': self.code,
            },
            'basic_properties': {
                'brand': data.get('brand', {}).get('display_data'),
                'actuator_variety': data.get('pneumatic_actuator_variety', {}).get('display_data'),
            },
            'selected_options': {
                'safety_position': data.get('safety_position', {}).get('display_data'),
                'springs_qty': data.get('springs_qty', {}).get('display_data'),
                'temperature': data.get('temperature', {}).get('display_data'),
                'ip': data.get('ip', {}).get('display_data'),
                'exd': data.get('exd', {}).get('display_data'),
                'body_coating': data.get('body_coating', {}).get('display_data'),
                'hand_wheel': data.get('hand_wheel', {}).get('display_data'),
            },
            'calculated_parameters': {
                'weight': data.get('weight', {}).get('display_data'),
                'time_to_close': data.get('time_to_close', {}).get('display_data'),
            },
            'torque_thrust_table': data.get('torque_thrust_table', {}).get('data'),
            'formatted': {
                'short': self._generate_short_description(),
                'technical': self._generate_tech_description(),
                'html': self._generate_html_description(),
            }
        }
        return structured_data

    @property
    def generated_model_item_code(self) -> str:
        """
        Генерирует артикул (code) по шаблону model_line.model_item_code_template.
        Поддерживает переменные: {model_code}, {springs_qty}, {temperature},
        {safety_position}, {hand_wheel}, {coating}, {ip}, {exd}.
        Если шаблон отсутствует — вызывает _generate_fallback_code().
        """
        if not self.selected_model_line_item or not self.selected_model_line_item.model_line:
            return self.code or ""

        template = self.selected_model_line_item.model_line.model_item_code_template
        if not template:
            return self._generate_fallback_code()

        result = template
        # Для всех опций encoding берётся из through-моделей (не code реальных опций)
        result = result.replace('{model_code}', self._get_value_old('selected_model_line_item__name'))
        result = result.replace('{springs_qty}', self._get_option_encoding('selected_springs_qty'))
        result = result.replace('{temperature}', self._get_option_encoding('selected_temperature'))
        result = result.replace('{safety_position}', self._get_option_encoding('selected_safety_position'))
        result = result.replace('{hand_wheel}', self._get_option_encoding('selected_hand_wheel'))
        result = result.replace('{coating}', self._get_option_encoding('selected_body_coating'))
        result = result.replace('{ip}', self._get_option_encoding('selected_ip'))
        result = result.replace('{exd}', self._get_option_encoding('selected_exd'))

        # Очистка
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\.\s+', ' ', result)
        result = re.sub(r'\s*\(DA\)', '', result)

        return result

    def _get_option_encoding(self, field_name: str) -> str:
        """
        Возвращает encoding опции из through-модели (не code реальной опции!).
        Для code-генерации важно брать encoding — он задаётся в through-моделях
        и соответствует шаблону артикула (например 'NO', а не 'no').
        """
        config = self._OPTION_CONFIG.get(field_name)
        if not config:
            return ''
        option_value = getattr(self, field_name)
        if not option_value:
            return ''

        through_attr = config.get('through_attr')
        if through_attr is None:
            # Temperature: through-модель САМА опция → encoding прямо на ней
            return getattr(option_value, 'encoding', '') or ''

        # Остальные: ищем through-запись по ID реальной опции + родителю
        ThroughModel = self._import_through_model(config)
        parent_obj = self._get_parent_for_option(config)
        if not parent_obj:
            return ''
        through_instance = ThroughModel.objects.filter(
            **{f'{through_attr}_id': option_value.id, config['parent_field']: parent_obj}
        ).first()
        return through_instance.encoding if through_instance and through_instance.encoding else ''

    def _get_value_old(self, field_path: str) -> str:
        """
        Обход цепочки атрибутов через двойное подчёркивание.
        Например, 'selected_springs_qty__code' → self.selected_springs_qty.code.
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

    def _generate_fallback_code(self) -> str:
        """Простая резервная генерация кода"""
        parts = [
            self._get_value_old('selected_model_line_item__code'),
            self._get_option_encoding('selected_springs_qty'),
            self._get_option_encoding('selected_temperature'),
            self._get_option_encoding('selected_safety_position'),
            self._get_option_encoding('selected_hand_wheel'),
            self._get_option_encoding('selected_body_coating'),
            self._get_option_encoding('selected_ip'),
            self._get_option_encoding('selected_exd'),
        ]
        return '.'.join(filter(None, parts))

    def _adjust_for_duplicate(self):
        """
        Добавляет суффикс (copy#XX) к name и code при обнаружении дубликата.
        Номер инкрементируется относительно существующих копий в базе.
        """
        if not self.name:
            return

        import re
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

    def save(self, *args, **kwargs):
        """
        Сохраняет конструктор с полным lifecycle:
        1. Валидация и автозаполнение опций через through-модели.
        2. Синхронизация work_temp_min/max из выбранной температуры.
        3. Автогенерация name, code, description.
        4. Проверка на дубликат — при совпадении добавляет суффикс (copy#XX).
        """
        # ЕДИНАЯ ВАЛИДАЦИЯ И КОРРЕКТИРОВКА ОПЦИЙ
        self._ensure_valid_options()

        # Синхронизация t° с выбранной температурной опцией
        if self.selected_temperature:
            self.work_temp_min = self.selected_temperature.work_temp_min
            self.work_temp_max = self.selected_temperature.work_temp_max

        # Генерация name/code/description ДО проверки дубликатов
        self.name = self.generated_model_item_code
        self.code = self.generated_model_item_code
        self.description = self._generate_short_description()

        # Проверка дубликатов — _adjust_for_duplicate добавит суффикс к уже сгенерированному
        duplicate_message = self._check_for_duplicates()
        if duplicate_message:
            self.is_unique = False
            self._adjust_for_duplicate()
            logger.warning(f"Создается дубликат: {duplicate_message}")
        else:
            self.is_unique = True

        super().save(*args, **kwargs)

    # ==================== ВАЛИДАЦИЯ ОПЦИЙ ====================

    def _ensure_valid_options(self):
        """
        Гарантирует, что все опции валидны для текущей модели.
        Для полей с through_attr: запрашивает through-модель, извлекает реальную опцию.
        Для полей без through_attr (temperature): through-модель сама опция.
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
        Запрашивает through-модель по родителю (model_line или model_line_item),
        ищет запись с is_default=True, извлекает реальную опцию через through_attr.
        При отсутствии дефолтной — берёт первую активную.
        """
        try:
            ThroughModel = self._import_through_model(config)
            parent_obj = self._get_parent_for_option(config)
            if not parent_obj:
                return

            # Ищем дефолтную through-запись
            through_instance = ThroughModel.objects.filter(
                **{config['parent_field']: parent_obj, 'is_default': True, 'is_active': True}
            ).first()

            if not through_instance:
                # Фолбэк: любая активная
                through_instance = ThroughModel.objects.filter(
                    **{config['parent_field']: parent_obj, 'is_active': True}
                ).first()

            if through_instance:
                actual_option = self._get_actual_option_from_through(through_instance, config)
                if actual_option:
                    setattr(self, field_name, actual_option)

        except Exception as e:
            logger.error(f"Error setting default for {field_name}: {e}")

    def _validate_option(self, field_name, current_value, config):
        """
        Проверить, что выбранная опция доступна для текущей модели.
        Для through_attr=None (temperature): проверяет through-запись по ID.
        Для остальных: ищет through-запись, где through_attr_id == current_value.id
        и parent совпадает. При невалидности — заменяет на дефолтную.
        """
        try:
            ThroughModel = self._import_through_model(config)
            parent_obj = self._get_parent_for_option(config)
            if not parent_obj:
                return

            through_attr = config.get('through_attr')

            if through_attr is None:
                # Temperature: through-модель сама опция — проверяем по ID
                valid = ThroughModel.objects.filter(
                    id=current_value.id,
                    **{config['parent_field']: parent_obj, 'is_active': True}
                ).exists()
            else:
                # Остальные: через through-модель ищем совпадение по ID реальной опции
                filter_kwargs = {
                    f'{through_attr}_id': current_value.id,
                    config['parent_field']: parent_obj,
                    'is_active': True
                }
                valid = ThroughModel.objects.filter(**filter_kwargs).exists()

            if not valid:
                # Заменяем на дефолтную
                default_through = ThroughModel.objects.filter(
                    **{config['parent_field']: parent_obj, 'is_default': True, 'is_active': True}
                ).first()
                if not default_through:
                    default_through = ThroughModel.objects.filter(
                        **{config['parent_field']: parent_obj, 'is_active': True}
                    ).first()
                if default_through:
                    actual_option = self._get_actual_option_from_through(default_through, config)
                    if actual_option:
                        setattr(self, field_name, actual_option)

        except Exception as e:
            logger.error(f"Error validating {field_name}: {e}")

    def _get_parent_for_option(self, config):
        """Получить родительский объект для опции"""
        if config['parent_field'] == 'model_line':
            return getattr(self.selected_model_line_item, 'model_line', None)
        else:
            return self.selected_model_line_item

    def _check_for_duplicates(self):
        """
        Проверяет, существует ли уже запись с такой же моделью и набором опций.
        Учитывает как заполненные опции (FK-равенство), так и пустые (IS NULL).
        Возвращает сообщение с информацией о дубликате или None.
        """
        filters = {}

        # Модель привода — ключевой признак конфигурации
        if self.selected_model_line_item:
            filters['selected_model_line_item'] = self.selected_model_line_item

        for field_name in self.get_option_fields():
            field_value = getattr(self, field_name)
            if field_value:
                filters[field_name] = field_value
            else:
                filters[f'{field_name}__isnull'] = True

        if filters:
            duplicates = self.__class__.objects.filter(**filters)
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)
            if duplicates.exists():
                duplicate = duplicates.first()
                return f"Найдена похожая конфигурация: {duplicate} (ID: {duplicate.id})"

        return None

    def clean(self):
        """Мягкая валидация выбранных опций через through-модели"""
        logger.info("=== CONSTRUCTOR CLEAN: Starting validation")

        if not self.selected_model_line_item:
            return

        for field_name, config in self._OPTION_CONFIG.items():
            field_value = getattr(self, field_name)
            if field_value:
                try:
                    ThroughModel = self._import_through_model(config)

                    filter_kwargs = {'is_active': True}
                    parent_obj = self._get_parent_for_option(config)
                    if not parent_obj:
                        logger.warning(f"Cannot validate {field_name}: parent not available")
                        continue
                    filter_kwargs[config['parent_field']] = parent_obj

                    through_attr = config.get('through_attr')
                    if through_attr is None:
                        # Temperature: through-модель сама опция
                        filter_kwargs['id'] = field_value.id
                    else:
                        # Остальные: фильтруем по ID реальной опции
                        filter_kwargs[f'{through_attr}_id'] = field_value.id

                    valid_option = ThroughModel.objects.filter(**filter_kwargs).exists()
                    logger.info(f"=== CLEAN: {field_name} valid={valid_option}")

                    if not valid_option:
                        logger.warning(
                            f'Выбранная {config["label"]} не доступна для модели {self.selected_model_line_item}.'
                        )

                except Exception as e:
                    logger.error(f"Error validating {field_name}: {e}")

        logger.info("=== CONSTRUCTOR CLEAN: Validation completed")

    # ==================== DISPLAY PROPERTIES ====================

    @property
    def selected_model_display(self):
        """Человекочитаемое название выбранной модели привода."""
        return str(self.selected_model_line_item) if self.selected_model_line_item else "-"

    @property
    def safety_position_display(self):
        """Человекочитаемое название положения безопасности (НЗ/НО)."""
        return str(self.selected_safety_position) if self.selected_safety_position else "-"

    @property
    def springs_qty_display(self):
        """Человекочитаемое название количества пружин."""
        return str(self.selected_springs_qty) if self.selected_springs_qty else "-"

    @property
    def temperature_display(self):
        """Человекочитаемое название температурного исполнения."""
        return str(self.selected_temperature) if self.selected_temperature else "-"

    @property
    def ip_display(self):
        """Человекочитаемое название степени защиты IP."""
        return str(self.selected_ip) if self.selected_ip else "-"

    @property
    def exd_display(self):
        """Человекочитаемое название взрывозащиты."""
        return str(self.selected_exd) if self.selected_exd else "-"

    @property
    def body_coating_display(self):
        """Человекочитаемое название покрытия корпуса."""
        return str(self.selected_body_coating) if self.selected_body_coating else "-"

    # ==================== GET AVAILABLE OPTIONS ====================

    def get_available_options(self) -> Dict[str, List[Dict]]:
        """
        Получить все доступные опции для выбранной модели.
        Возвращает словарь: ключ — имя поля опции, значение — список {id, option_id, name, code, is_default, ...}.
        option_id — это ID реальной опции (для подстановки в FK Конструктора).
        Для temperature: id и option_id совпадают (through-модель сама опция).
        """
        from pneumatic_actuators.models.pa_options import (
            PneumaticSafetyPositionOption, PneumaticSpringsQtyOption,
            PneumaticTemperatureOption, PneumaticIpOption,
            PneumaticExdOption, PneumaticBodyCoatingOption, PneumaticHandWheelOption
        )

        if not self.selected_model_line_item:
            return {}

        result = {}

        # Опции через model_line_item
        safety_through = PneumaticSafetyPositionOption.objects.filter(
            model_line_item=self.selected_model_line_item,
            is_active=True
        ).select_related('safety_position')

        result['safety_positions'] = [
            {
                'id': opt.id,                         # ID through-записи
                'option_id': opt.safety_position.id,   # ID реальной опции (params.SafetyPositionOption)
                'encoding': opt.encoding,
                'name': opt.safety_position.name,
                'code': opt.safety_position.code,
                'description': opt.description,
                'is_default': opt.is_default,
            }
            for opt in safety_through
        ]

        springs_through = PneumaticSpringsQtyOption.objects.filter(
            model_line_item=self.selected_model_line_item,
            is_active=True
        ).select_related('springs_qty')

        result['springs_qty_options'] = [
            {
                'id': opt.id,
                'option_id': opt.springs_qty.id,       # ID реальной опции (PneumaticActuatorSpringsQty)
                'encoding': opt.encoding,
                'name': opt.springs_qty.name,
                'code': opt.springs_qty.code,
                'description': opt.description,
                'is_default': opt.is_default,
            }
            for opt in springs_through
        ]

        # Опции через model_line
        if self.selected_model_line_item.model_line:
            ml = self.selected_model_line_item.model_line

            temp_through = PneumaticTemperatureOption.objects.filter(
                model_line=ml, is_active=True
            )
            result['temperature_options'] = [
                {
                    'id': opt.id,
                    'option_id': opt.id,               # Temperature: through-модель САМА опция
                    'encoding': opt.encoding,
                    'name': str(opt),
                    'work_temp_min': opt.work_temp_min,
                    'work_temp_max': opt.work_temp_max,
                    'description': opt.description,
                    'is_default': opt.is_default,
                }
                for opt in temp_through
            ]

            ip_through = PneumaticIpOption.objects.filter(
                model_line=ml, is_active=True
            ).select_related('ip_option')
            result['ip_options'] = [
                {
                    'id': opt.id,
                    'option_id': opt.ip_option.id,      # ID реальной опции (params.IpOption)
                    'encoding': opt.encoding,
                    'name': opt.ip_option.name,
                    'code': opt.ip_option.code,
                    'description': opt.description,
                    'is_default': opt.is_default,
                }
                for opt in ip_through
            ]

            exd_through = PneumaticExdOption.objects.filter(
                model_line=ml, is_active=True
            ).select_related('exd_option')
            result['exd_options'] = [
                {
                    'id': opt.id,
                    'option_id': opt.exd_option.id,
                    'encoding': opt.encoding,
                    'name': opt.exd_option.name,
                    'code': opt.exd_option.code,
                    'description': opt.description,
                    'is_default': opt.is_default,
                }
                for opt in exd_through
            ]

            coating_through = PneumaticBodyCoatingOption.objects.filter(
                model_line=ml, is_active=True
            ).select_related('body_coating_option')
            result['body_coating_options'] = [
                {
                    'id': opt.id,
                    'option_id': opt.body_coating_option.id,
                    'encoding': opt.encoding,
                    'name': opt.body_coating_option.name,
                    'code': opt.body_coating_option.code,
                    'description': opt.description,
                    'is_default': opt.is_default,
                }
                for opt in coating_through
            ]

            hw_through = PneumaticHandWheelOption.objects.filter(
                model_line=ml, is_active=True
            ).select_related('hand_wheel_option')
            result['hand_wheel_options'] = [
                {
                    'id': opt.id,
                    'option_id': opt.hand_wheel_option.id,
                    'encoding': opt.encoding,
                    'name': opt.hand_wheel_option.name,
                    'code': opt.hand_wheel_option.code,
                    'description': opt.description,
                    'is_default': opt.is_default,
                }
                for opt in hw_through
            ]

        return result

    # ==================== ВЕС ====================

    def get_weight(self) -> Optional[Decimal]:
        """
        Рассчитывает вес привода.
        Для DA (двойного действия): берёт вес из PneumaticWeightParameter с code='DA'.
        Для SR (с возвратной пружиной): вычисляет от максимального веса минус разница пружин × вес_одной.
        Возвращает None если недостаточно данных.
        """
        try:
            if not self.selected_model_line_item or not self.selected_model_line_item.body:
                return None

            body = self.selected_model_line_item.body
            from pneumatic_actuators.models import PneumaticWeightParameter

            # Для приводов DA
            if (self.selected_model_line_item.pneumatic_actuator_variety and
                    self.selected_model_line_item.pneumatic_actuator_variety.code == 'DA'):
                da_weight = PneumaticWeightParameter.objects.filter(
                    body=body,
                    spring_qty__code='DA'
                ).first()
                return da_weight.weight if da_weight else None

            # Для приводов SR
            if not self.selected_springs_qty:
                return None

            max_springs_qty = PneumaticWeightParameter.objects.filter(
                body=body
            ).exclude(spring_qty__code='DA').order_by('-spring_qty__code').first()

            if not max_springs_qty:
                return None

            # В Constructor: selected_springs_qty — это напрямую PneumaticActuatorSpringsQty
            if self.selected_springs_qty.code == max_springs_qty.spring_qty.code:
                return max_springs_qty.weight

            try:
                selected_springs = int(self.selected_springs_qty.code)
                max_springs = int(max_springs_qty.spring_qty.code)
                spring_difference = max_springs - selected_springs

                if body.weight_spring and spring_difference > 0:
                    return max_springs_qty.weight - (spring_difference * body.weight_spring)
                else:
                    return max_springs_qty.weight

            except (ValueError, TypeError):
                return max_springs_qty.weight

        except Exception:
            return None

    @property
    def calculated_weight(self) -> Optional[Decimal]:
        """Рассчитанный вес (property)"""
        return self.get_weight()

    # ==================== ДУБЛИРОВАНИЕ ====================

    def create_duplicate(self):
        """
        Создать полную копию текущей конфигурации.
        Копирует все FK опций, генерирует новый name/code через save(),
        затем добавляет суффикс (copy#XX) через _adjust_for_duplicate().
        Возвращает сохранённый объект-дубликат.
        """
        duplicate = self.__class__(
            selected_model_line=self.selected_model_line,
            selected_model_line_item=self.selected_model_line_item,
            selected_safety_position=self.selected_safety_position,
            selected_springs_qty=self.selected_springs_qty,
            selected_temperature=self.selected_temperature,
            selected_ip=self.selected_ip,
            selected_exd=self.selected_exd,
            selected_body_coating=self.selected_body_coating,
            selected_hand_wheel=self.selected_hand_wheel,
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