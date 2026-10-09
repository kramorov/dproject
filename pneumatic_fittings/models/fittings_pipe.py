# pneumatic_fittings/fittings_pipe.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.smart_catalog_mixin import  FilterDefinition , FilterType , DataSourceType
from materials.models import MaterialGeneral

from pneumatic_fittings.models.abstract_models import AbstractPneumaticFittingModelLine, AbstractPneumaticFitting
from pneumatic_fittings.models.fitting_parameters import FittingShape, FittingFixationMethod
from pneumatic_fittings.filters import _COMMON_FILTER_DEFINITIONS

class PneumaticFittingModelLine(AbstractPneumaticFittingModelLine):
    """Серия пневматических фитингов (резьба-трубка).

    Серия = конкретное сочетание «форма + способ фиксации» (прямой цанговый и т.п.),
    поэтому форма и способ задаются здесь, а позиции их наследуют.
    """

    shape = models.ForeignKey(FittingShape , related_name='pneumatic_fitting_model_lines' ,
                              blank=True , null=True ,
                              on_delete=models.SET_NULL ,
                              help_text=_('Форма фитинга') ,
                              verbose_name=_("Форма"))
    fixation_method = models.ForeignKey(FittingFixationMethod , related_name='pneumatic_fitting_model_lines_fixation' ,
                                        blank=True , null=True ,
                                        on_delete=models.SET_NULL ,
                                        help_text=_('Способ фиксации фитинга') ,
                                        verbose_name=_("Способ фиксации"))
    is_swivel = models.BooleanField(default=False ,
                                    verbose_name=_("Поворотный") ,
                                    help_text=_('Поворотное исполнение серии фитингов'))

    class Meta :
        ordering = ['brand' , 'code']
        verbose_name = _('Серия пневматических фитингов')
        verbose_name_plural = _('Серии пневматических фитингов')



class PneumaticFitting(AbstractPneumaticFitting):
    """Пневматический фитинг (резьба-трубка, вид 'fitting-thread-pipe')."""

    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'equipment_type', 'temperature_range',
        'shape', 'fixation_method', 'swivel', 'pressure_range',
        'pipe_diameter', 'thread', 'thread_inner_outer',
        'body_material', 'pipe_material', 'pressure_min', 'pressure_max',
        'temp_min', 'temp_max', 'weight', 'width_across_flats',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name',
        'shape', 'fixation_method',
        'thread', 'thread_inner_outer', 'body_material', 'temperature_range',
        'swivel', 'pipe_diameter', 'pipe_material', 'pressure_range',
        'pressure_min', 'pressure_max', 'temp_min', 'temp_max',
        'weight', 'width_across_flats',
    )

    config_hash_fields = (
        'model_line', 'body_material', 'pipe_material',
        'pipe_diameter', 'thread', 'thread_inner_outer',
    )

    model_line = models.ForeignKey(PneumaticFittingModelLine , related_name='pneumaticfitting_items' ,
                                   blank=True , null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия') ,
                                   verbose_name=_("Серия"))
    pipe_material = models.ForeignKey(MaterialGeneral , related_name='pneumatic_fitting_pipe_material' , blank=True ,
                                      null=True ,
                                      on_delete=models.SET_NULL ,
                                      help_text=_('Трубка') ,
                                      verbose_name=_('Тип материала трубки'))
    pipe_diameter = models.IntegerField(blank=True , null=True ,
                                        help_text=_('Диаметр') ,
                                        verbose_name=_('Диаметр трубки, мм'))

    class Meta :
        ordering = ['pipe_diameter' , 'thread']
        verbose_name = _('Пневматический фитинг')
        verbose_name_plural = _('Пневматические фитинги')


    FILTER_DEFINITIONS = _COMMON_FILTER_DEFINITIONS + [
        FilterDefinition(
            param_name='shape_id' ,
            model_field='model_line__shape' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Форма фитинга' ,
            order=8
        ) ,
        FilterDefinition(
            param_name='fixation_method_id' ,
            model_field='model_line__fixation_method' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Способ фиксации' ,
            order=9
        ) ,
        FilterDefinition(
            param_name='pipe_material_id' ,
            model_field='pipe_material' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Материал трубки' ,
            order=10
        ) ,
        FilterDefinition(
            param_name='pipe_diameter' ,
            model_field='pipe_diameter' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Диаметр трубки' ,
            order=11
        ) ,
        FilterDefinition(
            param_name='swivel' ,
            model_field='model_line__is_swivel' ,
            filter_type=FilterType.BOOLEAN ,
            data_source_type=DataSourceType.CHOICES ,
            choices=[('true', 'Поворотный'), ('false', 'Неповоротный')] ,
            label='Поворотность' ,
            order=12
        ) ,
    ]

    SEARCH_FIELDS = ['code']
    SELECT_RELATED_FIELDS = [
        'model_line__brand' , 'model_line' , 'model_line__shape' , 'model_line__fixation_method' ,
        'body_material' , 'pipe_material' , 'thread' , 'thread_inner_outer'
    ]

