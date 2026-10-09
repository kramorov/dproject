# pneumatic_fittings/silencers.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from pneumatic_fittings.models import PlugSilencerBodyMaterial
from pneumatic_fittings.models.abstract_models import AbstractPneumaticFittingModelLine, AbstractPneumaticFitting
from pneumatic_fittings.filters import _COMMON_FILTER_DEFINITIONS

class PneumaticPlugModelLine(AbstractPneumaticFittingModelLine):
    """Серия заглушек пневматических."""
    # body_material = models.ForeignKey(PlugSilencerBodyMaterial, related_name='plug_body_material',
    #                                   blank=True, null=True,
    #                                   on_delete=models.SET_NULL,
    #                                   help_text=_('Материал корпуса'),
    #                                   verbose_name=_("Материал корпуса"))
    class Meta :
        ordering = ['brand' , 'code']
        verbose_name = _('Серия заглушек пневматических')
        verbose_name_plural = _('Серии заглушек пневматических')


class PneumaticPlug(AbstractPneumaticFitting):
    """Заглушка пневматическая (вид 'fitting-plug')."""

    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'equipment_type', 'temperature_range',
        'thread', 'thread_inner_outer', 'pressure_range',
        'body_material', 'pressure_min', 'pressure_max',
        'temp_min', 'temp_max', 'weight', 'width_across_flats',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name',
        'thread', 'thread_inner_outer', 'body_material', 'temperature_range',
        'pressure_range', 'pressure_min', 'pressure_max', 'temp_min', 'temp_max',
        'weight', 'width_across_flats',
    )

    config_hash_fields = (
        'model_line', 'body_material', 'thread', 'thread_inner_outer',
    )

    model_line = models.ForeignKey(PneumaticPlugModelLine , related_name='pneumaticplug_items' ,
                                   blank=True , null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия') ,
                                   verbose_name=_("Серия"))

    class Meta :
        ordering = ['thread']
        verbose_name = _('Заглушка пневматическая')
        verbose_name_plural = _('Заглушки пневматические')

    FILTER_DEFINITIONS = _COMMON_FILTER_DEFINITIONS

    SEARCH_FIELDS = ['code']
    SELECT_RELATED_FIELDS = [
        'model_line__brand' , 'model_line' ,
        'body_material' , 'thread' , 'thread_inner_outer'
    ]
