# pa_controls/models/limit_switch.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Any

import logging

from core.models.catalog_mixin import CatalogFilterMixin, FilterFieldConfig, CommonFilterConfigs
from core.models.mixins import TemplateMixin
from materials.models import MaterialGeneral, MaterialSpecified
from pa_controls.models import LimitSwitchSensorVariety, LimitSwitchBody, \
    SensorComponent
from pa_controls.models.lsb_model_line import LimitSwitchModelLine
# from pa_controls.models import PaControlMountingStandard

logger = logging.getLogger(__name__)

from params.models import IpOption


# ============================================================
# БЛОК КОНЦЕВЫХ ВЫКЛЮЧАТЕЛЕЙ (Limit Switch Box)
# ============================================================


class LimitSwitchBox(CatalogFilterMixin, TemplateMixin, models.Model):
    """Модель блока концевых выключателей (каталог)
    points: int,
        1 точка - один датчик (обычно только на закрыто)
        2 точки - два датчика (на открыто и на закрыто) - самый распространенный вариант
        3 точки - три датчика (открыто, закрыто, промежуточное положение)
        4 точки - четыре датчика (два промежуточных положения + концевые)
    """
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
    # Добавляем Many-to-Many связь с датчиками
    sensor_components = models.ManyToManyField(
        SensorComponent,
        blank=True,
        verbose_name=_("Датчики"),
        help_text=_("Установленные датчики"),
        related_name='limit_switch_boxes'  # обратная связь от датчика к корпусам
    )

    points = models.IntegerField(default=2,
                                 verbose_name=_("Количество датчиков"),
                                 help_text=_("Количество точек переключения (датчиков)")
                                 )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, null=True,
                           related_name='limit_switch_box_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    exd = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='limit_switch_boxes',
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
    has_visual_indicator = models.BooleanField(default=False, verbose_name=_("Визуальный индикатор"))

    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        verbose_name = _("Блок концевых выключателей")
        verbose_name_plural = _("Блоки концевых выключателей")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

    def copy(self, suffix=" (Копия)", code_suffix="_copy"):
        """
        Создает копию текущего объекта

        Args:
            suffix: суффикс для name
            code_suffix: суффикс для code

        Returns:
            LimitSwitchBox: Скопированный объект
        """
        # Генерируем новые имена с суффиксом
        original_name = self.name or ""
        original_code = self.code or ""

        # Для name
        if suffix in original_name:
            base_name = original_name.replace(suffix, "")
            new_name = f"{base_name}{suffix}"
        else:
            new_name = f"{original_name}{suffix}"

        # Для code
        if original_code:
            if code_suffix in original_code:
                # Увеличиваем номер копии
                import re
                match = re.search(rf"{code_suffix}(\d+)$", original_code)
                if match:
                    num = int(match.group(1)) + 1
                    new_code = re.sub(rf"{code_suffix}\d+$", f"{code_suffix}{num}", original_code)
                else:
                    new_code = f"{original_code}{code_suffix}1"
            else:
                new_code = f"{original_code}{code_suffix}"
        else:
            new_code = None

        # Создаем копию
        copy = LimitSwitchBox(
            name=new_name,
            code=new_code,
            description=f"Копия: {self.description}" if self.description else "Копия",
            sorting_order=self.sorting_order + 100,
            is_active=self.is_active,
            model_line=self.model_line,
            body=self.body,
            sensor_variety=self.sensor_variety,
            points=self.points,
            ip=self.ip,
            work_temp_min=self.work_temp_min,
            work_temp_max=self.work_temp_max,
            body_material=self.body_material,
            body_material_specified=self.body_material_specified,
            is_pneumatic=self.is_pneumatic,
            has_namur_interface=self.has_namur_interface,
            has_visual_indicator=self.has_visual_indicator,
            extra_params=self.extra_params if self.extra_params else {}
        )
        copy.save()

        # Копируем ManyToMany поле exd
        copy.exd.set(self.exd.all())
        # Копируем ManyToMany поле sensor_components
        copy.exd.set(self.sensor_components.all())
        return copy

    @property
    def exd_display(self):
        """Возвращает отображаемую маркировку взрывозащиты"""
        if not self.exd.exists():
            return "Нет"

        return ", ".join([req.name for req in self.exd.all()])

    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand};  {points} датчика, тип датчика: {sensor_variety}; {ip}, Взрывозащита: {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material_specified}, Датчик: {sensors}, Отверстия под КВ:{cable_glands_holes}, вес {weight} кг."
        return default_description_template

    def _get_default_description_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand}; {points} датчика, тип датчика: {sensor_variety}, {ip}, Взрывозащита: {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material_specified}, Отверстия под КВ:{cable_glands_holes}, Монтаж:{mounting}, вес {weight}кг. Датчики: {sensors_description}"
        return default_description_template

    @property
    def get_sensors_description_list(self) -> str:
        """
        Возвращает  список поля description датчиков.
        Разделитель - символ "+"
        """
        sensor_components = self.sensor_components.all()
        if not sensor_components:
            return ""

        names = [item.description for item in sensor_components]
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]}; + {names[1]}"
        else:
            return ", ".join(names[:-1]) + f" + {names[-1]}"
    @property
    def get_sensors_names_list(self) -> str :
        """
        Возвращает текстовый список датчиков.
        Разделитель - символ "+"
        """
        sensor_components = self.sensor_components.all()
        if not sensor_components :
            return ""

        names = [item.generate_name() for item in sensor_components]

        if len(names) == 1 :
            return names[0]
        elif len(names) == 2 :
            return f"{names[0]}; + {names[1]}"
        else :
            return ", ".join(names[:-1]) + f" + {names[-1]}"

    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{sensor_variety}': 'sensor_variety',
            '{points}': 'points',
            '{body_material}': 'body_material',
            '{body_material_specified}': 'body_material_specified',
            '{weight}': 'body__weight',
            '{cable_glands_holes}': 'body__cable_glands_holes_list_text',
            '{mounting}': 'body__mounting_list_text',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
            '{exd}': 'exd_display',
            '{ip}': 'ip',
            # M2M поле - вызов метода get_sensors_list с подшаблоном
            # В подшаблоне можно использовать поля из SensorComponent (name, brand, signal_type, electrical_specs и т.д.)
            '{sensors}' : 'get_sensors_names_list' ,
            '{sensors_description}': 'get_sensors_description_list',
        }

    # ========== КОНФИГУРАЦИЯ ДЛЯ МИКСИНА CatalogFilterMixin ==========

    # 1. Конфигурация фильтров
    FILTER_CONFIG = [
        # Прямые поля
        FilterFieldConfig('model_line_id', 'model_line', 'exact'),
        FilterFieldConfig('sensor_variety_id', 'sensor_variety', 'exact'),
        FilterFieldConfig('points', 'points', 'exact'),

        FilterFieldConfig('body_material_id', 'body_material', 'exact'),
        FilterFieldConfig('body_material_specified_id', 'body_material_specified', 'exact'),

        # Температурные фильтры
        CommonFilterConfigs.temp_min_filter('work_temp_min'),
        CommonFilterConfigs.temp_max_filter('work_temp_max'),

        # IP фильтр - выбираем IP из списка, ищем с рангом >=
        CommonFilterConfigs.ip_rank_gte_filter(
            param_name='ip_id',  # Параметр получает ID выбранного IP
            rank_field='ip_rank',
            related_path='ip'
        ),

        # Фильтр по бренду (через model_line)
        FilterFieldConfig(
            param_name='model_line_brand_id',
            model_field='model_line__brand',
            filter_type='exact',
            is_related_field=True
        ),
    ]

    # 2. Поля для текстового поиска
    SEARCH_FIELDS = ['code', 'name', 'description']

    # 3. Поля для оптимизации запросов
    SELECT_RELATED_FIELDS = [
        'model_line',
        'model_line__brand',
        'sensor_variety',
        'ip',
        'body_material',
        'body_material_specified',
    ]

    # 4. Поля для prefetch (ManyToMany)
    PREFETCH_FIELDS = [
        'exd',
        'sensor_components',
    ]

    @classmethod
    def get_filter_options(cls) -> Dict[str, List[Dict]]:
        """Получить все доступные опции для фильтрации в UI"""
        result = {
            # Прямые ForeignKey поля
            'model_lines': cls.get_distinct_values('model_line'),
            'sensor_varieties': cls.get_distinct_values('sensor_variety'),
            'ip_options': cls.get_global_options(IpOption),
            'body_materials': cls._get_foreign_key_options('body_material'),
            'body_materials_specified': cls._get_foreign_key_options('body_material_specified'),

            # Бренд через model_line
            'model_line_brands': cls._get_foreign_key_options('model_line__brand'),

            # Choice поля (points от 1 до 4)
            'points_options': [
                {'id': 1, 'name': '1 датчик', 'code': '1'},
                {'id': 2, 'name': '2 датчика', 'code': '2'},
                {'id': 3, 'name': '3 датчика', 'code': '3'},
                {'id': 4, 'name': '4 датчика', 'code': '4'},
            ],

            # Булевы опции
            'boolean_options': [
                {'id': 'true', 'name': 'Да', 'code': 'true'},
                {'id': 'false', 'name': 'Нет', 'code': 'false'},
            ],

            # Диапазоны значений
            'work_temp_range': cls._get_value_range('work_temp_min'),
        }
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация БКВ"""
        return {
            # Базовые поля
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'sorting_order': self.sorting_order,
            'is_active': self.is_active,

            # Связанные модели
            'model_line': {
                'id': self.model_line.id,
                'name': self.model_line.name,
                'code': getattr(self.model_line, 'code', ''),
                'brand': {
                    'id': self.model_line.brand.id,
                    'name': self.model_line.brand.name,
                } if self.model_line and self.model_line.brand else None
            } if self.model_line else None,

            'sensor_variety': {
                'id': self.sensor_variety.id,
                'name': self.sensor_variety.name,
            } if self.sensor_variety else None,

            'ip': {
                'id': self.ip.id,
                'name': self.ip.name,
                'code': self.ip.code
            } if self.ip else None,

            'body_material': {
                'id': self.body_material.id,
                'name': self.body_material.name,
            } if self.body_material else None,

            'body_material_specified': {
                'id': self.body_material_specified.id,
                'name': self.body_material_specified.name,
            } if self.body_material_specified else None,

            # Характеристики
            'points': self.points,
            'work_temp_min': self.work_temp_min,
            'work_temp_max': self.work_temp_max,

            # Булевы поля
            'is_pneumatic': self.is_pneumatic,
            'has_namur_interface': self.has_namur_interface,
            'has_visual_indicator': self.has_visual_indicator,

            # ManyToMany поля
            'exd': [
                {
                    'id': exd.id,
                    'name': exd.name,
                    'code': exd.code
                }
                for exd in self.exd.all()
            ],
            'exd_display': self.exd_display,

            'sensor_components': [
                {
                    'id': sensor.id,
                    'name': sensor.generate_name() if hasattr(sensor, 'generate_name') else sensor.name,
                    'description': sensor.description
                }
                for sensor in self.sensor_components.all()
            ],
            'sensors_description': self.get_sensors_description_list,
            'sensors_names': self.get_sensors_names_list,

            # Дополнительно
            'extra_params': self.extra_params or {},
        }