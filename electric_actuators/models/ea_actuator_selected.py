# electric_actuators/models/ea_actuator_selected.py

from django.db import models
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from typing import List, Optional, Tuple, Any, Dict, Union
from decimal import Decimal
from django.core.exceptions import ValidationError
import re
from tabulate import tabulate

import logging
from django.utils.html import format_html

from electric_actuators.models import ElectricActuatorModelLineItem, CableGlandHolesSet, ElectricSafetyPositionOption
from params.models import MountingPlateTypes, StemShapes, StemSize

logger = logging.getLogger(__name__)

# Добавляем импорт абстрактного класса
from core.models import StructuredDataMixin


class ElectricActuatorSelected(StructuredDataMixin, models.Model):
    """
    Выбранный из списка моделей привод с выбранными опциями.
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

    selected_model_line_item = models.ForeignKey(ElectricActuatorModelLineItem,
                                                 related_name='selected_electric_actuator_model_line_item',
                                                 on_delete=models.CASCADE,
                                                 verbose_name=_('Модель'),
                                                 help_text=_('Модель электропривода'))

    actual_mounting_plate = models.ForeignKey(MountingPlateTypes, on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name='selected_mounting_plate',
                                              help_text='Монтажная площадка')
    actual_stem_shape = models.ForeignKey(StemShapes, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='selected_stem_shape',
                                          help_text='Тип отверстия под шток арматуры')
    actual_stem_size = models.ForeignKey(StemSize, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='selected_stem_size',
                                         help_text='Размер отверстия под шток арматуры')
    actual_cable_glands_holes = models.ForeignKey(CableGlandHolesSet, related_name='selected_cable_glands_holes',
                                                  on_delete=models.SET_NULL, null=True, blank=True,
                                                  help_text='Отверстия под кабельные вводы')

    # actual_wiring_diagram = models.ForeignKey('WiringDiagram' , related_name='actual_wiring_diagram' ,
    #                                           on_delete=models.SET_NULL , null=True , blank=True ,
    #                                           help_text='Схема подключения')

    # Выбранные опции
    selected_safety_position = models.ForeignKey(
        ElectricSafetyPositionOption,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Выбранное положение безопасности"),
        help_text=_('Выбранное положение безопасности привода')
    )

    # НОВЫЕ ОПЦИИ через model_line
    selected_temperature = models.ForeignKey(
        'ElectricTemperatureOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Температурная опция"),
        help_text=_('Выбранная температурная опция')
    )

    selected_ip = models.ForeignKey(
        'ElectricIpOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Степень защиты IP"),
        help_text=_('Выбранная степень защиты IP')
    )

    selected_exd = models.ForeignKey(
        'ElectricExdOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Взрывозащита"),
        help_text=_('Выбранная опция взрывозащиты')
    )

    selected_body_coating = models.ForeignKey(
        'ElectricBodyCoatingOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Покрытие корпуса"),
        help_text=_('Выбранное покрытие корпуса')
    )

    selected_hand_wheel = models.ForeignKey(
        'ElectricHandWheelOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Встроенный дублер"),
        help_text=_('Встроенный ручной дублер')
    )

    selected_turn_angle_option = models.ForeignKey(
        'ElectricTurnAngleOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Угол поворота"),
        help_text=_('Угол поворота')
    )

    selected_power_supply = models.ForeignKey(
        'ElectricPowerSupplyOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Напряжение"),
        help_text=_('Напряжение питания')
    )
    selected_cable_glands_holes = models.ForeignKey(
        'CableGlandHolesSetBodyOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Кабельные вводы"),
        help_text=_('Отверстия под кабельные вводы')
    )
    selected_control_unit_option = models.ForeignKey(
        'ElectricControlUnitOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Блок управления"),
        help_text=_("Выбранный блок управления с кодировкой")
    )

    is_unique = models.BooleanField(default=True, verbose_name='Это уникальная конфигурация')

    # ОБЩАЯ КОНФИГУРАЦИЯ ДЛЯ ВСЕХ ВАЛИДАЦИЙ
    _OPTION_CONFIG = {
        # 'selected_safety_position': {
        #     'model_class': 'ElectricTemperatureOption',
        #     'label': 'положение безопасности',
        #     'parent_field': 'model_line_item',  # Для связи с моделью
        #     'model_path': 'electric_actuators.models.ea_options.ElectricTemperatureOption'
        # },
        'selected_temperature': {
            'model_class': 'ElectricTemperatureOption',
            'label': 'температурная опция',
            'parent_field': 'model_line',  # Здесь model_line, а не model_line_item
            'model_path': 'electric_actuators.models.ea_options.ElectricTemperatureOption'
        },
        'selected_ip': {
            'model_class': 'ElectricIpOption',
            'label': 'степень защиты IP',
            'parent_field': 'model_line',
            'model_path': 'electric_actuators.models.ea_options.ElectricIpOption'
        },
        'selected_exd': {
            'model_class': 'ElectricExdOption',
            'label': 'взрывозащита',
            'parent_field': 'model_line',
            'model_path': 'electric_actuators.models.ea_options.ElectricExdOption'
        },
        'selected_body_coating': {
            'model_class': 'ElectricBodyCoatingOption',
            'label': 'покрытие корпуса',
            'parent_field': 'model_line',
            'model_path': 'electric_actuators.models.ea_options.ElectricBodyCoatingOption'
        },
        'selected_turn_angle_option': {
            'model_class': 'ElectricTurnAngleOption',
            'label': 'угол поворота',
            'parent_field': 'model_line',
            'model_path': 'electric_actuators.models.ea_options.ElectricTurnAngleOption'
        },
        'selected_hand_wheel': {
            'model_class': 'ElectricHandWheelOption',
            'label': 'ручной дублер',
            'parent_field': 'model_line',
            'model_path': 'electric_actuators.models.ea_options.ElectricHandWheelOption'
        },
        'selected_power_supply': {
            'model_class': 'ElectricPowerSupplyOption',
            'label': 'напряжение питания',
            'parent_field': 'model_line_item',
            'model_path': 'electric_actuators.models.ea_model_line_item_options.ElectricPowerSupplyOption'
        },
        # ДОБАВЛЯЕМ КОНФИГ ДЛЯ НОВОГО ПОЛЯ
        'selected_control_unit_option': {
            'model_class': 'ElectricControlUnitOption',
            'label': 'опция блока управления',
            'parent_field': 'power_supply_option',  # Фильтр по выбранному напряжению
            'model_path': 'electric_actuators.models.ea_model_line_item_options.ElectricControlUnitOption',
            'dynamic_filter': True  # Флаг что фильтр динамический
        },
    }

    @property
    def selected_control_unit_installed(self):
        """Получить выбранный блок управления"""
        if self.selected_control_unit_option:
            return self.selected_control_unit_option.control_unit
        return None

    @property
    def selected_control_encoding(self):
        """Получить кодировку выбранного блока управления"""
        if self.selected_control_unit_option:
            return self.selected_control_unit_option.encoding
        return ""

    @classmethod
    def get_option_fields(cls):
        """Возвращает список всех полей опций"""
        return list(cls._OPTION_CONFIG.keys())

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Модель электропривода selected')
        verbose_name_plural = _('Модели электропривода selected')

    def __str__(self):
        return self.name

    def _get_value(self, field_path: str) -> str:
        """Простое получение значения поля"""
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
        """Простая резервная генерация
            AR19E001.S24.LT.IP67.INT/N.220/50.Ex """
        parts = [
            self._get_value('selected_model__code'),
            self._get_value('selected_temperature__encoding'),
            self._get_value('selected_ip__encoding'),
            self._get_value('selected_ip__encoding'),
            self._get_value('selected_control_unit_installed__encoding'),
            # self._get_value('selected_safety_position__encoding'),
            # self._get_value('selected_hand_wheel__encoding'),
            # self._get_value('selected_body_coating__encoding'),

            self._get_value('selected_exd__encoding'),
        ]
        # Фильтруем пустые значения и соединяем
        return '.'.join(filter(None, parts))

    def generated_model_item_code(self):
        """Сгенерировать артикул по шаблону из model_line"""
        if not self.selected_model_line_item or not self.selected_model_line_item.model_line:
            return self.code or ""

        # Проверьте, что self.selected_model_line_item здесь еще объект
        print(f"=== DEBUG generated_model_item_code ===")
        print(f"self.selected_model_line_item: {self.selected_model_line_item}")
        print(f"type: {type(self.selected_model_line_item)}")

        template = self.selected_model_line_item.model_line.model_item_code_template
        if not template:
            print(f"Template for {self.selected_model_line_item.model_line} not found. Generating from fallback")
            return self._generate_fallback_code()

        """Простой рендеринг шаблона - заменяем переменные значениями"""
        result = template
        print(f"template: {result}")
        # Простая замена переменных  AR19E001.S24.LT.IP67.INT/N.220/50.Ex
        # {model_code}{temperature}{ip}{voltage}{exd}
        result = result.replace('{model_code}', self._get_value('selected_model_line_item__name'))
        result = result.replace('{temperature}', self._get_value('selected_temperature__encoding'))
        result = result.replace('{ip}', self._get_value('selected_ip__encoding'))
        if self.selected_control_unit_option:
            selected_control_unit_option_encoding = self.selected_control_unit_option.encoding
            print(f"selected_control_unit_option_encoding: {selected_control_unit_option_encoding}")
            # Кодировка уже хранится в through-модели
            result = result.replace('{control_unit}', selected_control_unit_option_encoding)

        # self._get_value('selected_control_unit_installed__encoding'),
        # result = result.replace('{hand_wheel}', self._get_value('selected_hand_wheel__encoding'))
        # result = result.replace('{coating}', self._get_value('selected_body_coating__encoding'))

        result = result.replace('{voltage}', self._get_value('selected_power_supply__encoding'))
        result = result.replace('{exd}', self._get_value('selected_exd__encoding'))

        print(f"До очистки: {result}")
        # Очистка лишних точек (две точки подряд -> одна точка)
        result = re.sub(r'\.{2,}', '.', result)
        print(f"две точки подряд -> одна точка: {result}")
        # Удаляем точку в начале и конце
        result = re.sub(r'\.\s+', ' ', result)  # Заменяет точку и любые пробельные символы после нее
        print(f"удалили точки в начале и конце: {result}")

        return result

    def get_available_options(self):
        """Получить все доступные опции для выбранной модели"""
        # print(f"DEBUG get_available_options: Called for {self.id if self.id else 'new'}")

        if not self.selected_model_line_item:
            # print("DEBUG get_available_options: No selected_model_line_item")
            return self._get_empty_options()

        try:
            result = {}
            # print(f"DEBUG get_available_options: Processing options from _OPTION_CONFIG")

            # Получаем информацию о model_line для отладки
            model_line_info = None
            if hasattr(self.selected_model_line_item, 'model_line'):
                model_line_info = self.selected_model_line_item.model_line
                # print(f"DEBUG get_available_options: Model line: {model_line_info}")

            # Для каждой опции из _OPTION_CONFIG
            for field_name, config in self._OPTION_CONFIG.items():
                # print(f"\nDEBUG get_available_options: Processing {field_name}")
                # print(f"DEBUG get_available_options: Config: {config}")

                try:
                    # Динамически импортируем модель
                    module_path, class_name = config['model_path'].rsplit('.', 1)
                    # print(f"DEBUG get_available_options: Importing {class_name} from {module_path}")

                    module = __import__(module_path, fromlist=[class_name])
                    model_class = getattr(module, class_name)
                    # print(f"DEBUG get_available_options: Model class loaded: {model_class}")

                    # Определяем ключ для результата
                    result_key = f"{field_name}_options".replace('selected_', '')
                    # print(f"DEBUG get_available_options: Result key: {result_key}")

                    # Особый случай: опция блока управления зависит от выбранного напряжения
                    if field_name == 'selected_control_unit_option':
                        if not self.selected_power_supply:
                            # print("DEBUG get_available_options: No power supply selected for control unit options")
                            result[result_key] = []
                            continue

                        # Фильтруем по выбранному напряжению
                        filter_kwargs = {
                            'power_supply_option': self.selected_power_supply,
                            'is_active': True
                        }
                        # print(
                        # f"DEBUG get_available_options: Filter by power_supply_option: {self.selected_power_supply.id}")

                    elif config['parent_field'] == 'model_line':
                        if model_line_info:
                            filter_kwargs = {
                                config['parent_field']: model_line_info,
                                'is_active': True
                            }
                            # print(f"DEBUG get_available_options: Filter by model_line: {model_line_info.id}")
                        else:
                            # print(f"DEBUG get_available_options: No model_line, skipping")
                            result[result_key] = []
                            continue

                    elif config['parent_field'] == 'model_line_item':
                        filter_kwargs = {
                            config['parent_field']: self.selected_model_line_item,
                            'is_active': True
                        }
                        # print(
                        # f"DEBUG get_available_options: Filter by model_line_item: {self.selected_model_line_item.id}")

                    else:
                        # Для других связей
                        parent_value = getattr(self.selected_model_line_item, config['parent_field'], None)
                        if parent_value:
                            filter_kwargs = {config['parent_field']: parent_value, 'is_active': True}
                            # print(f"DEBUG get_available_options: Filter by {config['parent_field']}: {parent_value}")
                        else:
                            # print(f"DEBUG get_available_options: No {config['parent_field']}, skipping")
                            result[result_key] = []
                            continue

                    # Получаем опции
                    # print(f"DEBUG get_available_options: Filter kwargs: {filter_kwargs}")
                    options = model_class.objects.filter(**filter_kwargs)
                    count = options.count()
                    # print(f"DEBUG get_available_options: Found {count} options")

                    # Формируем список опций
                    options_list = []
                    for opt in options:
                        option_data = {
                            'id': opt.id,
                            'encoding': opt.encoding or '',
                            'name': str(opt),
                            'description': opt.description or '',
                            'is_default': getattr(opt, 'is_default', False),
                            'parent_field': config['parent_field']
                        }

                        # Для опций блока управления добавляем дополнительную информацию
                        if field_name == 'selected_control_unit_option':
                            if hasattr(opt, 'control_unit'):
                                option_data['control_unit_name'] = str(opt.control_unit)
                                option_data['control_unit_id'] = opt.control_unit.id

                        options_list.append(option_data)

                    result[result_key] = options_list

                    # Логируем первые 3 опции для отладки
                    if count > 0:
                        # print(f"DEBUG get_available_options: First 3 options:")
                        for i, opt in enumerate(options_list[:3]):
                            print(f"  {i + 1}. {opt['name']} (id: {opt['id']}, encoding: {opt['encoding']})")

                except ImportError as e:
                    print(f"ERROR get_available_options: Failed to import {config['model_path']}: {e}")
                    result_key = f"{field_name}_options".replace('selected_', '')
                    result[result_key] = []
                except AttributeError as e:
                    print(f"ERROR get_available_options: Attribute error for {field_name}: {e}")
                    result_key = f"{field_name}_options".replace('selected_', '')
                    result[result_key] = []
                except Exception as e:
                    print(f"ERROR get_available_options: Unexpected error for {field_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    result_key = f"{field_name}_options".replace('selected_', '')
                    result[result_key] = []

            # print(f"\nDEBUG get_available_options: Final result keys: {list(result.keys())}")
            for key, value in result.items():
                print(f"  {key}: {len(value)} items")

            return result

        except Exception as e:
            print(f"CRITICAL ERROR in get_available_options: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Critical error in get_available_options: {e}")
            return self._get_empty_options()

    def _get_empty_options(self):
        """Пустые опции на основе _OPTION_CONFIG"""
        result = {}

        for field_name in self._OPTION_CONFIG.keys():
            result_key = f"{field_name}_options".replace('selected_', '')
            result[result_key] = []
            # print(f"DEBUG _get_empty_options: Added empty list for {result_key}")

        return result

    def _get_related_data(self) -> Dict[str, Any]:
        """Связанные данные"""
        related_data = {}

        # Данные модели
        if self.selected_model_line_item and hasattr(self.selected_model_line_item, 'get_compact_data'):
            related_data['selected_model'] = self.selected_model_line_item.get_compact_data()

        # Данные опций (используем _OPTION_CONFIG для перебора)
        for option_field in self.get_option_fields():
            field = getattr(self, option_field)
            if field and hasattr(field, 'get_compact_data'):
                related_data[option_field] = field.get_compact_data()

        # Доступные опции
        related_data['available_options'] = self.get_available_options()

        return related_data

    def _check_for_duplicates(self):
        """Проверка на дубликаты в базе данных"""
        if not self.pk:  # Только для новых записей
            # Собираем фильтры для всех полей опций
            filters = {}

            # Основное поле - модель
            if self.selected_model_line_item:
                filters['selected_model_line_item'] = self.selected_model_line_item

            # Опции через model_line
            for field_name in self.get_option_fields():
                field_value = getattr(self, field_name)
                if field_value:  # Только если значение установлено
                    filters[field_name] = field_value
                else:
                    # Для NULL значений используем __isnull
                    filters[f'{field_name}__isnull'] = True

            # Добавляем конструктивные особенности
            if self.actual_stem_shape:
                filters['actual_stem_shape'] = self.actual_stem_shape
            else:
                filters['actual_stem_shape__isnull'] = True

            if self.actual_stem_size:
                filters['actual_stem_size'] = self.actual_stem_size
            else:
                filters['actual_stem_size__isnull'] = True

            if self.actual_cable_glands_holes:
                filters['actual_cable_glands_holes'] = self.actual_cable_glands_holes
            else:
                filters['actual_cable_glands_holes__isnull'] = True

            # Монтажные площадки (ManyToMany) - сложнее для проверки
            # Пока пропускаем

            # Если есть хотя бы одно поле для фильтрации
            if filters:
                # Ищем дубликаты
                duplicates = ElectricActuatorSelected.objects.filter(**filters)

                # Исключаем самого себя если это обновление
                if self.pk:
                    duplicates = duplicates.exclude(pk=self.pk)

                if duplicates.exists():
                    duplicate = duplicates.first()
                    return f"Найдена похожая конфигурация: {duplicate} (ID: {duplicate.id})"

        return None

    def _adjust_for_duplicate(self):
        """Настройка для дублирующей конфигурации"""
        if not self.name:
            return

        import re

        # Определяем следующий номер для копии
        base_name_for_search = re.sub(r'\s*\(copy\s*#\d+\)$', '', self.name, flags=re.IGNORECASE).strip()

        # Ищем все существующие копии с таким же базовым именем
        from django.db.models import Q
        existing_copies = self.__class__.objects.filter(
            Q(name=self.name) |
            Q(name__iregex=r'^' + re.escape(base_name_for_search) + r'\s*\(copy\s*#\d+\)$')
        )

        # Определяем максимальный номер копии
        max_number = 0
        for copy in existing_copies:
            match = re.search(r'\(copy\s*#(\d+)\)$', copy.name, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                max_number = max(max_number, num)
            elif copy.name == self.name:
                # Если есть точное совпадение, это тоже считается копией
                max_number = max(max_number, 1)

        new_number = max_number + 1

        # Форматируем номер с ведущими нулями (01, 02, ...)
        formatted_number = f"{new_number:02d}"

        # Обновляем имя: добавляем (copy#XX) к существующему имени
        self.name = f"{self.name} (copy#{formatted_number})"

        # Обновляем код: добавляем (copy#XX) к существующему коду
        if self.code:
            # Убираем возможные предыдущие суффиксы copy
            clean_code = re.sub(r'\s*\(copy\s*#\d+\)$', '', self.code, flags=re.IGNORECASE)
            self.code = f"{clean_code} (copy#{formatted_number})"

    def create_duplicate(self):
        """Создать дубликат текущего объекта"""
        duplicate = self.__class__(
            # Копируем ForeignKey поля
            selected_model_line_item=self.selected_model_line_item,
            selected_temperature=self.selected_temperature,
            selected_ip=self.selected_ip,
            selected_exd=self.selected_exd,
            selected_body_coating=self.selected_body_coating,
            selected_hand_wheel=self.selected_hand_wheel,

            # Копируем конструктивные особенности
            actual_mounting_plate=self.actual_mounting_plate.all(),
            actual_stem_shape=self.actual_stem_shape,
            actual_stem_size=self.actual_stem_size,
            actual_cable_glands_holes=self.actual_cable_glands_holes,

            # Копируем остальные поля
            sorting_order=self.sorting_order,
            is_active=self.is_active,
            is_unique=False,

            # Пустые поля - будут сгенерированы автоматически в save()
            name='',
            code='',
            description=self.description
        )

        # Сохраняем - автоматически сгенерируются name и code
        duplicate.save()

        # Сохраняем ManyToMany поле
        duplicate.actual_mounting_plate.set(self.actual_mounting_plate.all())

        # Теперь добавляем суффикс к уже сгенерированному имени и коду
        if duplicate.name:
            duplicate._adjust_for_duplicate()
            duplicate.save()

        return duplicate

    def _generate_short_description(self) -> Dict[str, Any]:
        """Получить структурированные данные для описания
        model_line_data = {
            'name': {'display_name':'Название серии', 'value':self.code if self.code else None},
            'default_output_type': {'display_name':'Тип привода', 'value':self.default_output_type.name if self.default_output_type else None},
            'brand': {'display_name':'Бренд', 'value':self.brand.name  if self.brand else None}
        }
        model_line_item_data = {
            'time_to_open': {'display_name':'Время открытия', 'value':self.time_to_open if self.time_to_open else None},
            'time_to_close': {'display_name':'Время закрытия', 'value':self.time_to_close if self.time_to_close else None},
            'rotation_speed': {'display_name':'Скорость вращения, об/мин', 'value':self.rotation_speed if self.rotation_speed else None},
            'torque_min': {'display_name':'Вращающий момент мин, Нм', 'value':self.torque_min if self.torque_min else None},
            'torque_max': {'display_name':'Вращающий момент макс, Нм', 'value':self.torque_max if self.torque_max else None}
        }
        body_data = {
            'mounting_plate': {'display_name':'Монтажные площадки', 'value':self.mounting_plate_display},
            'stem_shape': {'display_name':'Форма отверстия под шток', 'value':self.stem_shape if self.stem_shape else None},
            'stem_size': {'display_name':'Размер отверстия под шток', 'value':self.stem_size if self.stem_size else None},
            'max_stem_height': {'display_name':'Максимальная высота штока', 'value':self.max_stem_height if self.max_stem_height else None},
            'max_stem_diameter': {'display_name':'Максимально возможный диаметр штока', 'value':self.max_stem_diameter if self.max_stem_diameter else None},
            'weight_body': {'display_name':'Вес корпуса', 'value':self.weight_body if self.weight_body else None},
        }
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"EA logger get_description_data")
        print(f"EA  print _generate_short_description")
        model_line_data = self.selected_model_line_item.model_line.get_description_data()
        model_line_item_data = self.selected_model_line_item.get_description_data()
        body_data = self.selected_model_line_item.body.get_description_data()

        data = {
            'model': {'display_name': 'Артикул модели:',
                      'name': self.code if self.code else None
                      },
            'brand': {
                'display_name': model_line_data.get('display_name', 'Бренд'),
                'value': model_line_data.get('value', '')
            },
            'cable_glands_holes': {
                'display_name': 'Кабельные вводы',
                'value': None,
                'is_default': True
            },
            'mounting_plate': {'display_name': 'Монтажные площадки', 'value': body_data['mounting_plate']['value'],
                               'is_default': True},
            'stem_shape': {'display_name': 'Форма отверстия под шток',
                           'value': None,
                           'is_default': True},
            'stem_size': {'display_name': 'Размер отверстия под шток',
                          'value': body_data['stem_size']['value'],
                          'is_default': True},
            'max_stem_height': {'display_name': 'Максимальная высота штока',
                                'value': None,  # type: ignore  # будет заполнено позже
                                'is_default': True},
            'max_stem_diameter': {'display_name': 'Максимально возможный диаметр штока',
                                  'value': None,
                                  'is_default': True},
            'power_supply': {'display_name': 'Напряжение питания, В',
                             'value': None},
            'motor_current_rated': {'display_name': 'Ток номинальный, А', 'value': None},
            'motor_current_starting': {'display_name': 'Пусковой ток, А', 'value': None},
            'motor_power': {'display_name': 'Мощность электродвигателя, кВт', 'value': None},
            'time_to_open': model_line_item_data['time_to_open'],
            'time_to_close': model_line_item_data['time_to_close'],
            'torque_min': model_line_item_data['torque_min'],
            'torque_max': model_line_item_data['torque_max'],
        }
        if self.actual_mounting_plate:
            data['mounting_plate']['value'] = self.actual_mounting_plate.name
            data['mounting_plate']['is_default'] = False
        if self.actual_stem_shape:
            print(f'actual_stem_shape {self.actual_stem_shape} name {self.actual_stem_shape.name}')
            data['stem_shape']['value'] = str(self.actual_stem_shape.name)
            data['stem_shape']['is_default'] = False
        if self.actual_stem_size:
            data['stem_size']['value'] = self.actual_stem_size.name
            data['stem_size']['is_default'] = False
        if self.selected_power_supply:
            power_supply_data = self.selected_power_supply.get_description_data()
            data['power_supply']['value'] = power_supply_data['power_supply']['value']

            if power_supply_data['time_to_open']['value'] > 0 or power_supply_data['time_to_close']['value'] > 0:
                data['time_to_open']['value'] = power_supply_data['time_to_open']['value']
                data['time_to_close']['value'] = power_supply_data['time_to_close']['value']
                if data['time_to_close']['value'] == 0:
                    data['time_to_close']['value'] = data['time_to_open']['value']
                if data['time_to_open']['value'] == 0:
                    data['time_to_open']['value'] = data['time_to_close']['value']

            if power_supply_data['torque_min']['value'] > 0 or power_supply_data['torque_max']['value'] > 0:
                data['torque_min']['value'] = power_supply_data['torque_min']['value']
                data['torque_max']['value'] = power_supply_data['torque_max']['value']

        # Добавить обработку cable_glands_holes если они есть в INT блоке
        print(f'cable_glands_holes {data['cable_glands_holes']['value']}')

        if self.actual_cable_glands_holes:
            data['cable_glands_holes']['value'] = self.actual_cable_glands_holes.get_description_data()

        print(data['cable_glands_holes']['value'])

        if self.selected_ip:
            data['ip_data'] = self.selected_ip.get_description_data()

        if self.selected_exd:
            data['exd_data'] = self.selected_exd.get_description_data()

        if self.selected_safety_position:
            data['selected_safety_position'] = self.selected_safety_position.get_description_data()

        if self.selected_temperature:
            data['selected_temperature'] = self.selected_temperature.get_description_data()

        if self.selected_body_coating:
            data['selected_body_coating'] = self.selected_body_coating.get_description_data()

        if self.selected_hand_wheel:
            data['selected_hand_wheel'] = self.selected_hand_wheel.get_description_data()

        if self.selected_turn_angle_option:
            data['selected_turn_angle_option'] = self.selected_turn_angle_option.get_description_data()

        if self.selected_control_unit_option:
            data['selected_control_unit_option'] = self.selected_control_unit_option.get_description_data()
        print(f'data={data}')
        return data

    def save(self, *args, **kwargs):
        print(f"\n=== DEBUG save() called ===")
        print(f"Object ID: {self.id}")
        print(f"selected_model_line_item: {self.selected_model_line_item}")
        print(f"selected_temperature: {self.selected_temperature}")
        print(f"selected_ip: {self.selected_ip}")
        print(f"selected_exd: {self.selected_exd}")
        print(f"selected_power_supply: {self.selected_power_supply}")
        try:
            # Получаем оригинальный объект
            original = None
            if self.pk:
                try:
                    original = self.__class__._default_manager.get(pk=self.pk)
                    print(f"Original exists: {original}")
                except self.__class__.DoesNotExist:
                    print("Original not found")
                    pass

            # Применяем дефолтные опции
            self.apply_default_options()

            # Генерируем код
            new_code = self.generated_model_item_code()
            print(f"Generated code: {new_code}")

            if new_code:
                self.code = new_code
                self.name = new_code
            else:
                print("WARNING: No code generated, keeping existing")

            # Проверяем уникальность
            duplicate_message = self._check_for_duplicates()
            if duplicate_message:
                self.is_unique = False
                self._adjust_for_duplicate()
                logger.warning(f"Создается дубликат: {duplicate_message}")
            else:
                self.is_unique = True

            # Валидация полей
            self.clean()

            # Автозаполнение полей
            if not self.description:
                self.description = self._generate_short_description() if hasattr(self,
                                                                                 '_generate_short_description') else ""

            # Сохраняем
            print(f"Final code before save: {self.code}")
            super().save(*args, **kwargs)
            print("=== save() completed ===")

        except Exception as e:
            # Логируем ошибку
            logger.error(f"Error saving ElectricActuatorSelected: {e}")
            import traceback
            traceback.print_exc()
            # Пробрасываем исключение дальше
            raise

    def apply_default_options(self):
        """Применить дефолтные опции из выбранной модели"""
        if not self.selected_model_line_item:
            return

        try:
            model_line = self.selected_model_line_item.model_line
            if not model_line:
                return

            print(f"DEBUG: Applying default options for model line: {model_line}")

            # Для каждой опции ищем дефолтное значение
            for option_field, config in self._OPTION_CONFIG.items():
                current_value = getattr(self, option_field)
                if not current_value:  # Если опция не выбрана
                    try:
                        # Динамически импортируем модель опции
                        module_path, class_name = config['model_path'].rsplit('.', 1)
                        module = __import__(module_path, fromlist=[class_name])
                        model_class = getattr(module, class_name)

                        # Ищем дефолтную опцию
                        filter_kwargs = {
                            config['parent_field']: model_line,
                            'is_default': True,
                            'is_active': True
                        }

                        default_option = model_class.objects.filter(**filter_kwargs).first()

                        if default_option:
                            setattr(self, option_field, default_option)
                            print(f"DEBUG: Set default {option_field} = {default_option}")
                        else:
                            # Если дефолтной нет, берем первую активную
                            filter_kwargs.pop('is_default')
                            first_option = model_class.objects.filter(**filter_kwargs).first()
                            if first_option:
                                setattr(self, option_field, first_option)
                                print(f"DEBUG: Set first active {option_field} = {first_option}")

                    except Exception as e:
                        print(f"DEBUG: Error setting default for {option_field}: {e}")

            print("DEBUG: Default options applied")

        except Exception as e:
            print(f"DEBUG: Error in apply_default_options: {e}")
            logger.error(f"Error in apply_default_options: {e}")
