#filter_requlator/models/fr_model_line_item.py
from typing import Dict, List, Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, TemplateMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin , FilterDefinition , FilterType , DataSourceType
from filter_regulator.models import FilterRegulatorBody
from filter_regulator.models.fr_model_line import FilterRegulatorModelLine
from filter_regulator.models.fr_options import FilterRegulatorVariety , DrainVariety


class FilterRegulator(SmartCatalogMixin,CopyMixin,TemplateMixin,  models.Model):
    """Модель фильтр-регулятора (каталог)"""
    name = models.TextField(blank=True ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название модели фильтр-регулятора'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели фильтр-регулятора"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели фильтр-регулятора'))

    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    GAUGE_CHOICES = [
        (0, _('Без манометра')),
        (1, _('1 манометр в комплекте')),
        (2, _('2 манометра в комплекте')),
    ]
    gauge_quantity = models.IntegerField(
        choices=GAUGE_CHOICES,
        default=1,
        verbose_name=_("Комплектация манометром")
    )

    model_line = models.ForeignKey(FilterRegulatorModelLine , related_name='filter_model_line' ,
                                   blank=True ,
                                   null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия модели фильтр-регулятора') ,
                                   verbose_name=_("Серия"))

    body = models.ForeignKey(FilterRegulatorBody , related_name='filter_body' ,
                                blank=True ,
                                null=True ,
                                on_delete=models.SET_NULL ,
                                help_text=_('Корпус фильтр-регулятора') ,
                                verbose_name=_("Корпус"))
    drain_variety = models.ForeignKey(DrainVariety , related_name='filter_drain_variety' ,
                                blank=True ,
                                null=True ,
                                on_delete=models.SET_NULL ,
                                help_text=_('Тип модели фильтр-регулятора') ,
                                verbose_name=_("Тип"))
    filtration_rating = models.DecimalField(
        max_digits=5 , decimal_places=1 ,
        null=True , blank=True ,
        verbose_name=_("Тонкость фильтрации (мкм)")
    )
    MATERIAL_CHOICES = [
        ('bronze' , 'Спеченная бронза') ,
        ('plastic' , 'Пористый полимер') ,
        ('ss' , 'Нержавеющая сетка') ,
    ]
    filter_element_material = models.CharField(max_length=20 , choices=MATERIAL_CHOICES , verbose_name=_("Материал фильтрующего элемента"))

    flow_rate = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name=_("Макс. расход (л/мин)")
    )
    WALL_MOUNTING_CHOICES = [
        ('no' , 'Нет') ,
        ('yes' , 'В комплекте') ,
    ]
    wall_mounting_included = models.CharField(max_length=20 , choices=WALL_MOUNTING_CHOICES, default='yes',
                                               verbose_name=_("Настенное крепление в комплекте"))
    has_shut_off_valve = models.BooleanField(default=False, verbose_name=_("Отсечной клапан в комплекте"))
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict , blank=True ,
        verbose_name=_("Параметры") ,
        help_text=_("signal_type, resistance, range и т.д.")
    )
    class Meta:
        verbose_name = _("Фильтр-регулятор")
        verbose_name_plural = _("Фильтр-регуляторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def copy(self):
        """ Переоределяем - вызываем функцию из миксина CopyMixin и передаем пароаметры
        Создает копию с суффиксом 'Копия' и сбросом sorting_order и is_active"""
        # return super().copy(suffix=" Копия", reset_fields=['sorting_order', 'is_active'])
        return super().copy(suffix=" Копия", reset_fields=[])

    @property
    def gauge_quantity_display(self):
        """Возвращает текстовое представление комплектации манометром"""
        return self.get_gauge_quantity_display()

    @property
    def wall_mounting_included_display(self):
        """Возвращает текстовое представление комплектации манометром"""
        return self.get_wall_mounting_included_display()

    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{flow_rate}': 'flow_rate',
            '{filter_variety}': 'model_line__filter_variety',
            '{pressure_min}': 'model_line__pressure_min',
            '{pressure_max}': 'model_line__pressure_max',
            '{pressure_inlet_max}': 'model_line__pressure_inlet_max',
            '{wall_mounting_included}': 'wall_mounting_included_display',
            '{body_material}': 'model_line__body_material',
            '{bowl_material}': 'model_line__bowl_material',
            '{bowl_material_text}': 'model_line__bowl_material_text',
            '{protection_material}': 'model_line__protection_material',
            '{body_material_specified}': 'body_material_specified',
            '{filter_element_material}': 'filter_element_material',
            '{filtration_rating}': 'filtration_rating',
            '{work_temp_min}': 'model_line__work_temp_min',
            '{work_temp_max}': 'model_line__work_temp_max',
            '{weight}': 'body__weight',
            '{thread}': 'body__thread',
            '{gauge_port_size}': 'body__gauge_port_size',
            '{drain_port_size}': 'body__drain_port_size',
            '{drain_variety}' : 'drain_variety' ,
            '{gauge_quantity}': 'gauge_quantity_display',
        }
    def _get_name_template_source(self):
        """Переоределяем в модели функцию из миксина CopyMixin: вернуть шаблон названия или None."""
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Переоределяем в модели функцию из миксина CopyMixin: вернуть шаблон описания или None."""
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        default_description_template = ("{model_code} {filter_variety} {brand}; Расход {flow_rate} л/мин; {drain_variety}; Т.окр. {work_temp_min}..{work_temp_max} °С, Рег.давления {pressure_min}..{pressure_max} бар; Порты: {thread}; фильтрация {filtration_rating} мкм;")
        return default_description_template

    def _get_default_description_template(self) -> str:
        default_description_template = ("{model_code} {filter_variety} {brand}; Расход {flow_rate} л/мин; {drain_variety}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material}, Материал стакана: {bowl_material_text}, Кожух: {protection_material} Порты: {thread}; слив: {drain_port_size}; {gauge_quantity}; фильтрация {filtration_rating} мкм; Диапазон регулировки давления {pressure_min}..{pressure_max} бар; Макс. входное давление {pressure_inlet_max} бар; вес {weight}кг. Настенное крепление: {wall_mounting_included}")
        return default_description_template

        # ========== КОНФИГУРАЦИЯ ДЛЯ МИКСИНА SmartCatalogMixin ==========

    FILTER_DEFINITIONS = [
        # --- Прямые ForeignKey ---
        FilterDefinition(
            param_name='model_line_id' ,
            model_field='model_line' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.FOREIGN_KEY ,
            label='Серия' ,
            order=1
        ) ,
        FilterDefinition(
            param_name='drain_variety_id' ,
            model_field='drain_variety' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.FOREIGN_KEY ,
            label='Тип дренажа' ,
            order=2
        ) ,

        # --- Choice-поля ---
        FilterDefinition(
            param_name='gauge_quantity' ,
            model_field='gauge_quantity' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.CHOICES ,
            source_field='gauge_quantity' ,
            label='Манометр' ,
            order=3
        ) ,
        FilterDefinition(
            param_name='filter_element_material' ,
            model_field='filter_element_material' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.CHOICES ,
            source_field='filter_element_material' ,
            label='Материал фильтр. элемента' ,
            order=4
        ) ,

        # --- Диапазонные (MIN/MAX) ---
        FilterDefinition(
            param_name='min_filtration_rating' ,
            model_field='filtration_rating' ,
            filter_type=FilterType.MIN ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Тонкость фильтрации от' ,
            order=5
        ) ,
        FilterDefinition(
            param_name='max_filtration_rating' ,
            model_field='filtration_rating' ,
            filter_type=FilterType.MAX ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Тонкость фильтрации до' ,
            order=6
        ) ,
        FilterDefinition(
            param_name='min_flow_rate' ,
            model_field='flow_rate' ,
            filter_type=FilterType.MIN ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Расход от' ,
            order=7
        ) ,
        FilterDefinition(
            param_name='max_flow_rate' ,
            model_field='flow_rate' ,
            filter_type=FilterType.MAX ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Расход до' ,
            order=8
        ) ,

        # --- Связанные ForeignKey (через body / model_line) ---
        FilterDefinition(
            param_name='body_thread_id' ,
            model_field='body__thread' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Резьба корпуса' ,
            order=9
        ) ,
        FilterDefinition(
            param_name='model_line_filter_variety_id' ,
            model_field='model_line__filter_variety' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Разновидность' ,
            order=10
        ) ,
        FilterDefinition(
            param_name='model_line_body_material_id' ,
            model_field='model_line__body_material' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Материал корпуса серии' ,
            order=11
        ) ,
        FilterDefinition(
            param_name='model_line_brand_id' ,
            model_field='model_line__brand' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Бренд серии' ,
            order=12
        ) ,

        # --- Температуры (TEMP_MIN = lte, TEMP_MAX = gte) ---
        FilterDefinition(
            param_name='model_line_work_temp_min' ,
            model_field='model_line__work_temp_min' ,
            filter_type=FilterType.TEMP_MIN ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Раб. температура от' ,
            order=13
        ) ,
        FilterDefinition(
            param_name='model_line_work_temp_max' ,
            model_field='model_line__work_temp_max' ,
            filter_type=FilterType.TEMP_MAX ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Раб. температура до' ,
            order=14
        ) ,

        # --- Давления (MAX=lte для user_min, MIN=gte для user_max) ---
        FilterDefinition(
            param_name='model_line_pressure_min' ,
            model_field='model_line__pressure_min' ,
            filter_type=FilterType.MAX ,  # lte: оборудование.pressure_min <= user_min
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Требуемое давление от' ,
            order=15
        ) ,
        FilterDefinition(
            param_name='model_line_pressure_max' ,
            model_field='model_line__pressure_max' ,
            filter_type=FilterType.MIN ,  # gte: оборудование.pressure_max >= user_max
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Требуемое давление до' ,
            order=16
        ) ,
        FilterDefinition(
            param_name='model_line_pressure_inlet_max' ,
            model_field='model_line__pressure_inlet_max' ,
            filter_type=FilterType.MIN ,  # gte
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Макс. входное давление' ,
            order=17
        ) ,
    ]

    SEARCH_FIELDS = ['code', 'name', 'description']

    SELECT_RELATED_FIELDS = [
        'model_line',
        'model_line__brand',  # ← добавили brand
        'model_line__filter_variety',
        'model_line__body_material',
        'body',
        'body__thread',
        'drain_variety',
    ]


    def to_dict(self) -> Dict[str, Any]:
        """Сериализация фильтр-регулятора"""
        return {
            # Базовые поля
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'sorting_order': self.sorting_order,
            'is_active': self.is_active,

            # Параметры
            'gauge_quantity': self.gauge_quantity,
            'gauge_quantity_display': self.get_gauge_quantity_display(),
            'filtration_rating': float(self.filtration_rating) if self.filtration_rating else None,
            'filter_element_material': self.filter_element_material,
            'filter_element_material_display': self.get_filter_element_material_display(),
            'flow_rate': float(self.flow_rate) if self.flow_rate else None,
            'wall_mounting_included': self.wall_mounting_included,
            'wall_mounting_included_display': self.get_wall_mounting_included_display(),
            'has_shut_off_valve': self.has_shut_off_valve,
            'extra_params': self.extra_params or {},

            # Связанные модели
            'model_line': {
                'id': self.model_line.id,
                'name': self.model_line.name,
                'code': getattr(self.model_line, 'code', ''),
                'brand' : {
                    'id' : self.model_line.brand.id ,
                    'name' : self.model_line.brand.name ,
                    'code' : getattr(self.model_line.brand , 'code' , '')
                } if self.model_line and self.model_line.brand else None ,
                'filter_variety': {
                    'id': self.model_line.filter_variety.id,
                    'name': self.model_line.filter_variety.name,
                } if self.model_line and self.model_line.filter_variety else None,
                'body_material': {
                    'id': self.model_line.body_material.id,
                    'name': self.model_line.body_material.name,
                } if self.model_line and self.model_line.body_material else None,
                'work_temp_min': self.model_line.work_temp_min if self.model_line else None,
                'work_temp_max': self.model_line.work_temp_max if self.model_line else None,
                'pressure_min': float(
                    self.model_line.pressure_min) if self.model_line and self.model_line.pressure_min is not None else None,
                'pressure_max': float(
                    self.model_line.pressure_max) if self.model_line and self.model_line.pressure_max is not None else None,
                'pressure_inlet_max': float(
                    self.model_line.pressure_inlet_max) if self.model_line and self.model_line.pressure_inlet_max is not None else None,
            } if self.model_line else None,

            'drain_variety': {
                'id': self.drain_variety.id,
                'name': self.drain_variety.name,
                'code': getattr(self.drain_variety, 'code', '')
            } if self.drain_variety else None,

            'body': {
                'id': self.body.id,
                'name': self.body.name,
                'code': getattr(self.body, 'code', ''),
                'thread': {
                    'id': self.body.thread.id,
                    'name': self.body.thread.name,
                    'code': self.body.thread.code
                } if self.body and self.body.thread else None
            } if self.body else None,
        }