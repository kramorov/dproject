#filter_requlator/models/fr_model_line_item.py
from typing import Dict, List, Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.catalog_mixin import CatalogFilterMixin, FilterFieldConfig, CommonFilterConfigs
from core.models.mixins import CopyMixin, TemplateMixin
from filter_regulator.models import FilterRegulatorBody
from filter_regulator.models.fr_model_line import FilterRegulatorModelLine
from filter_regulator.models.fr_options import FilterRegulatorVariety , DrainVariety
from params.models import ThreadSize


class FilterRegulator(CatalogFilterMixin,CopyMixin,TemplateMixin,  models.Model):
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

        # ========== КОНФИГУРАЦИЯ ДЛЯ МИКСИНА ==========

    FILTER_CONFIG = [
        # Прямые поля
        FilterFieldConfig('model_line_id', 'model_line', 'exact'),
        FilterFieldConfig('drain_variety_id', 'drain_variety', 'exact'),
        FilterFieldConfig('gauge_quantity', 'gauge_quantity', 'exact'),
        FilterFieldConfig('filter_element_material', 'filter_element_material', 'exact'),

        # Диапазонные фильтры
        CommonFilterConfigs.min_value_filter('filtration_rating', param_name='min_filtration_rating'),
        CommonFilterConfigs.max_value_filter('filtration_rating', param_name='max_filtration_rating'),
        CommonFilterConfigs.min_value_filter('flow_rate', param_name='min_flow_rate'),
        CommonFilterConfigs.max_value_filter('flow_rate', param_name='max_flow_rate'),

        # Фильтры по полям корпуса
        FilterFieldConfig('body_thread_id', 'body__thread', 'exact', is_related_field=True),

        # Фильтры по полям серии
        FilterFieldConfig('model_line_filter_variety_id', 'model_line__filter_variety', 'exact', is_related_field=True),
        FilterFieldConfig('model_line_body_material_id', 'model_line__body_material', 'exact', is_related_field=True),

        # Фильтр по бренду из model_line
        FilterFieldConfig('model_line_brand_id', 'model_line__brand', 'exact', is_related_field=True),
        # Фильтры по температуре связанные поля из model_line
        CommonFilterConfigs.temp_min_filter(
            field_name='work_temp_min',
            param_name='model_line_work_temp_min',
            is_related_field=True,
            related_path='model_line__work_temp_min'
        ),
        CommonFilterConfigs.temp_max_filter(
            field_name='work_temp_max',
            param_name='model_line_work_temp_max',
            is_related_field=True,
            related_path='model_line__work_temp_max'
        ),
        # Фильтры по давлению связанные поля из model_line
        # Для давления - используем min_value_filter и max_value_filter
        # Фильтры по давлению (диапазон должен перекрывать требуемый)
        # user_min_pressure - оборудование должно иметь минимальное давление НЕ ВЫШЕ (≤)
        CommonFilterConfigs.max_value_filter(  # ← lte
            field_name='pressure_min',
            param_name='model_line_pressure_min',
            related_path='model_line__pressure_min',
            is_related_field=True
        ),

        # pressure_max должно быть НЕ НИЖЕ (≥) требуемого максимума
        CommonFilterConfigs.min_value_filter(  # ← gte
            field_name='pressure_max',
            param_name='model_line_pressure_max',
            related_path='model_line__pressure_max',
            is_related_field=True
        ),

        # Максимальное входное давление
        CommonFilterConfigs.min_value_filter(  # ← gte
            field_name='pressure_inlet_max',
            param_name='model_line_pressure_inlet_max',
            related_path='model_line__pressure_inlet_max',
            is_related_field=True
        ),
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

    PREFETCH_FIELDS = []

    @classmethod
    def get_filter_options(cls) -> Dict[str, List[Dict]]:
        """Получить все доступные опции для фильтрации в UI"""
        result = {
            # Прямые ForeignKey поля
            'model_lines': cls.get_distinct_values('model_line'),
            'drain_varieties': cls.get_distinct_values('drain_variety'),

            # ForeignKey через get_foreign_key_options
            'body_thread_options': cls._get_foreign_key_options('body__thread'),
            'model_line_filter_varieties': cls._get_foreign_key_options('model_line__filter_variety'),
            'model_line_body_materials': cls._get_foreign_key_options('model_line__body_material'),
            'model_line_brands': cls._get_foreign_key_options('model_line__brand'),  # ← добавили

            # Choice поля
            'gauge_quantity_options': [
                {'id': 0, 'name': str(_('Без манометра')), 'code': '0'},
                {'id': 1, 'name': str(_('1 манометр в комплекте')), 'code': '1'},
                {'id': 2, 'name': str(_('2 манометра в комплекте')), 'code': '2'},
            ],

            # Диапазоны значений
            'filtration_rating_range': cls._get_value_range('filtration_rating'),
            'flow_rate_range': cls._get_value_range('flow_rate'),
            'model_line_pressure_range': cls._get_value_range('model_line__pressure_min'),
            'model_line_temp_range': cls._get_value_range('model_line__work_temp_min'),
        }
        return result

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
                    self.model_line.pressure_min) if self.model_line and self.model_line.pressure_min else None,
                'pressure_max': float(
                    self.model_line.pressure_max) if self.model_line and self.model_line.pressure_max else None,
                'pressure_inlet_max': float(
                    self.model_line.pressure_inlet_max) if self.model_line and self.model_line.pressure_inlet_max else None,
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