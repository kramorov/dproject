#gearbox/models/gearbox.py
from typing import Dict, List, Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.catalog_mixin import CatalogFilterMixin, FilterFieldConfig, CommonFilterConfigs
from core.models.mixins import CopyMixin, TemplateMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin, DataSourceType, FilterType, FilterDefinition
from params.models import LockingMechanism, IpOption, MountingPlateTypes


class GearBox(SmartCatalogMixin, CopyMixin,TemplateMixin,  models.Model):
    """Модель редуктора (каталог)"""
    name = models.TextField(blank=True ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название модели редуктора'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели редуктора"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели редуктора'))

    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey('gearbox.GearBoxModelLine' , related_name='gear_box_model_line' ,
                                   blank=True ,
                                   null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия модели редуктора') ,
                                   verbose_name=_("Серия"))

    body = models.ForeignKey(
        'gearbox.GearBoxBody',
        on_delete=models.SET_NULL,
        blank=True , null=True ,
        verbose_name=_("Корпус редуктора"),
        help_text=_("Корпус редуктора с писанием свойств")
    )
    body_material_text = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name=_("Материал корпуса")
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

    override_mechanism = models.ForeignKey(
        'OverrideMechanism',
        on_delete=models.SET_NULL,
        blank=True , null=True ,
        verbose_name=_("Механизм отключения"),
        help_text=_("Механизм отключения дублера")
    )
    locking_mechanism = models.ForeignKey(
        LockingMechanism,
        on_delete=models.SET_NULL,
        blank=True , null=True ,
        verbose_name=_("Механизм блокировки"),
        help_text=_("Механизм блокировки дублера/переключателя")
    )
    DECLUTCHABLE_CHOICES = (
        ('yes' , _('расцепляемый')) ,
        ('no' , _('не расцепляемый')) ,
    )

    is_declutchable = models.CharField(
        max_length=3 ,
        choices=DECLUTCHABLE_CHOICES ,
        default='yes' ,
        verbose_name=_("Расцепляемый (Declutchable)") ,
        help_text=_("Можно ли физически отсоединить штурвал от привода")
    )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, blank=True , null=True ,
                           related_name='gearbox_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    # Интерлок (лучше вынести в отдельную модель)
    interlock = models.ForeignKey('gearbox.GearBoxInterlock', on_delete=models.SET_NULL, null=True, blank=True,related_name='gearbox_interlock',
                           help_text=_('Модель интерлока'),
                           verbose_name=_("Модель интерлока")
                           )
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict , blank=True , null=True ,
        verbose_name=_("Параметры") ,
        help_text=_("signal_type, resistance, range и т.д.")
    )
    class Meta:
        verbose_name = _("Редуктор")
        verbose_name_plural = _("Редукторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

    @property
    def is_declutchable_display(self) :
        return dict(self.DECLUTCHABLE_CHOICES).get(self.is_declutchable , '')

    def copy(self):
        """ Переоределяем - вызываем функцию из миксина CopyMixin и передаем параметры
        Создает копию с суффиксом 'Копия' и сбросом sorting_order и is_active """
        copied_obj = super().copy(suffix=" Копия", reset_fields=['sorting_order', 'is_active'])
        # Если нужно скопировать и корпус (создать новый корпус)
        # if self.body:
        #     copied_obj.body = self.body.copy()
        #     copied_obj.body.save()
        return copied_obj

    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{gearbox_output_variety}': 'model_line__gearbox_output_variety',
            '{gearbox_variety}' : 'model_line__gearbox_variety' ,
            '{turn_angle}': 'model_line__turn_angle' ,
            '{turn_tuning_limit}': 'model_line__turn_tuning_limit' ,
            '{weight}' : 'body__weight' ,
            '{mechanical_advantage}' : 'body__mechanical_advantage' ,
            '{max_stem_diameter_bottom}' : 'body__max_stem_diameter_bottom',
            '{stem_height_bottom}' : 'body__stem_height_bottom' ,
            '{stem_size_bottom}' : 'body__stem_size_bottom' ,
            '{stem_shape_bottom}' : 'body__stem_shape_bottom' ,
            '{mounting_plate_bottom_list_text}' : 'body__mounting_plate_bottom_list_text' ,
            '{stem_height_top}' : 'body__stem_height_top' ,
            '{stem_size_top}' : 'body__stem_size_top' ,
            '{stem_shape_top}' : 'body__stem_shape_top' ,
            '{mounting_plate_top_list_text}' : 'body__mounting_plate_top_list_text' ,
            '{handwheel_diameter}' : 'body__handwheel_diameter' ,
            '{handwheel_force_nominal}' : 'body__handwheel_force_nominal' ,
            '{max_output_torque}' : 'body__max_output_torque' ,
            '{max_input_torque}' : 'body__max_input_torque' ,
            '{efficiency}': 'body__efficiency',
            '{amplification_factor}': 'body__amplification_factor',
            '{reduction_ratio_text}': 'body__reduction_ratio_text',
            '{transmission_variety}': 'body__transmission_variety',
            '{interlock}': 'interlock',
            '{ip}': 'ip',
            '{locking_mechanism}': 'locking_mechanism',
            '{is_declutchable}': 'is_declutchable_display',
            '{override_mechanism}': 'override_mechanism',
            '{body_material_text}': 'body_material_text',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
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

    # 1. Конфигурация фильтров
    FILTER_DEFINITIONS = [
        # Серия
        FilterDefinition(
            param_name='model_line_id',
            model_field='model_line',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.FOREIGN_KEY,
            label='Серия',
            order=1
        ),
           # IP (с ранжированием)
        FilterDefinition(
            param_name='ip_id',
            model_field='ip',
            filter_type=FilterType.IP_RANK,
            data_source_type=DataSourceType.GLOBAL_MODEL,
            source_model=IpOption,
            label='IP',
            order=4
        ),


        # Температура
        FilterDefinition(
            param_name='work_temp_min',
            model_field='work_temp_min',
            filter_type=FilterType.TEMP_MIN,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Температура от',
            order=5
        ),
        FilterDefinition(
            param_name='work_temp_max',
            model_field='work_temp_max',
            filter_type=FilterType.TEMP_MAX,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Температура до',
            order=6
        ),
        FilterDefinition(
            param_name='work_temp_max',
            model_field='work_temp_max',
            filter_type=FilterType.TEMP_MAX,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Температура до',
            order=6
        ),
        # Материалы
        FilterDefinition(
            param_name='body_material_id',
            model_field='body_material',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.FOREIGN_KEY,
            label='Материал корпуса',
            order=7
        ),

        # Бренд через серию
        FilterDefinition(
            param_name='model_line_brand_id',
            model_field='model_line__brand',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Бренд серии',
            order=8
        ),

        # Тип сигнала (датчики)
        # FilterDefinition(  #Все значения из глобальной модели
        #     param_name='signal_type_id',
        #     model_field='primary_sensor__signal_type',
        #     filter_type=FilterType.EXACT,
        #     data_source_type=DataSourceType.GLOBAL_MODEL,
        #     source_model=SignalType,
        #     label='Тип сигнала',
        #     order=9
        # ),
        # Только имеющиеся в справочнике
        # Для ForeignKey полей - используем UNIQUE_FIELD_VALUES (только используемые)
        FilterDefinition(
            param_name='signal_type_id',
            model_field='primary_sensor__signal_type',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,  # ← только используемые
            label='Тип сигнала',
            order=9
        ),
    ]




    # M2M_FILTER_CONFIG должен быть определен
    M2M_FILTER_CONFIG = [
        {
            'param_name': 'mounting_plate_top_id',
            'm2m_field': 'body__mounting_plate_top',
        },
    ]

    SEARCH_FIELDS = ['code', 'name', 'description']

    SELECT_RELATED_FIELDS = [
        'model_line', 'body',  'ip', #'interlock' - записей нет, поэтому не используем
    ]

    # PREFETCH_FIELDS = [
    #     'body__mounting_plate_top',
    #     'body__mounting_plate_bottom',
    # ]


    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализация редуктора с использованием to_dict() корпуса
        """
        return {
            # Базовые поля
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'sorting_order': self.sorting_order,
            'is_active': self.is_active,

            # Прямые связи
            'model_line': {
                'id': self.model_line.id,
                'name': self.model_line.name,
                'code': getattr(self.model_line, 'code', '')
            } if self.model_line else None,

            'override_mechanism': {
                'id': self.override_mechanism.id,
                'name': self.override_mechanism.name,
            } if self.override_mechanism else None,

            'locking_mechanism': {
                'id': self.locking_mechanism.id,
                'name': self.locking_mechanism.name,
            } if self.locking_mechanism else None,

            'ip': {
                'id': self.ip.id,
                'name': self.ip.name,
                'code': getattr(self.ip, 'code', '')
            } if self.ip else None,

            'interlock': {
                'id': self.interlock.id,
                'name': self.interlock.name,
            } if self.interlock else None,

            # Параметры работы
            'work_temp_min': self.work_temp_min,
            'work_temp_max': self.work_temp_max,
            'is_declutchable': self.is_declutchable,
            'is_declutchable_display': self.is_declutchable_display,

            # Дополнительные параметры
            'extra_params': self.extra_params or {},

            # Корпус - используем метод to_dict() модели корпуса
            'body': self.body.api_dict() if self.body else None,

            # Материал корпуса (текстовое поле из GearBox, а не из корпуса)
            'body_material_text': self.body_material_text,
        }



   # ========== КОНФИГУРАЦИЯ ДЛЯ МИКСИНА CatalogFilterMixin ==========
   #
   #  # 1. Конфигурация фильтров
   #  FILTER_CONFIG = [
   #      FilterFieldConfig('model_line_id', 'model_line', 'exact'),
   #      FilterFieldConfig('body_id', 'body', 'exact'),
   #      CommonFilterConfigs.temp_min_filter(
   #          field_name='work_temp_min',
   #          param_name='work_temp_min'
   #      ),
   #
   #      CommonFilterConfigs.temp_min_filter(
   #          field_name='work_temp_max',
   #          param_name='work_temp_max'
   #      ),
   #
   #      # Фильтры по полям GearBoxBody (через связанную модель)
   #      CommonFilterConfigs.min_value_filter(
   #          field_name='max_work_torque',
   #          param_name='min_work_torque',
   #          related_path='body__max_work_torque',
   #          is_related_field=True
   #      ),
   #      # IP фильтр - выбираем IP из списка, ищем с рангом >=
   #      CommonFilterConfigs.ip_rank_gte_filter(
   #          param_name='ip_id',  # Параметр получает ID выбранного IP
   #          rank_field='ip_rank',
   #          related_path='ip'
   #      ),
   #  ]
   #
   #  # M2M_FILTER_CONFIG должен быть определен
   #  M2M_FILTER_CONFIG = [
   #      {
   #          'param_name': 'mounting_plate_top_id',
   #          'm2m_field': 'body__mounting_plate_top',
   #      },
   #  ]
   #
   #  SEARCH_FIELDS = ['code', 'name', 'description']
   #
   #  SELECT_RELATED_FIELDS = [
   #      'model_line', 'body',  'ip', #'interlock' - записей нет, поэтому не используем
   #  ]
   #
   #  # PREFETCH_FIELDS = [
   #  #     'body__mounting_plate_top',
   #  #     'body__mounting_plate_bottom',
   #  # ]
   #
   #  @classmethod
   #  def get_filter_options(cls) -> Dict[str, List[Dict]]:
   #      """Получить все доступные опции для фильтрации в UI"""
   #      result = {
   #          'model_lines': cls.get_distinct_values('model_line'),
   #          'bodies': cls.get_distinct_values('body'),
   #          'override_mechanisms': cls.get_distinct_values('override_mechanism'),
   #          'locking_mechanisms': cls.get_distinct_values('locking_mechanism'),
   #          'ip_options': cls.get_global_options(IpOption),
   #          'mounting_plate_top_options': cls.get_global_options(MountingPlateTypes),
   #          'min_work_torque_range': cls._get_value_range('body__max_work_torque'),
   #      }
   #      return result
    #
    # @classmethod
    # def get_filter_options(cls) -> Dict[str, List[Dict]]:
    #     """Получить все доступные опции для фильтрации в UI"""
    #     result = {
    #         'model_lines': cls.get_distinct_values('model_line'),
    #         'bodies': cls.get_distinct_values('body'),
    #         'override_mechanisms': cls.get_distinct_values('override_mechanism'),
    #         'locking_mechanisms': cls.get_distinct_values('locking_mechanism'),
    #         'ip_options': cls.get_global_options(IpOption),
    #         'mounting_plate_top_options': cls.get_global_options(MountingPlateTypes),
    #         'min_work_torque_range': cls._get_value_range('body__max_work_torque'),
    #     }
    #     return result
