# pneumatic_fittings/silencer.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from pneumatic_fittings.models import PlugSilencerBodyMaterial, SilencerFilterElement, SilencerShape
from pneumatic_fittings.models.abstract_models import AbstractPneumaticFittingModelLine, AbstractPneumaticFitting
from pneumatic_fittings.filters import _COMMON_FILTER_DEFINITIONS

class PneumaticSilencerModelLine(AbstractPneumaticFittingModelLine):
    """Серия глушителей пневматических."""
    # body_material = models.ForeignKey(PlugSilencerBodyMaterial, related_name='pneumaticsilencer_body_material',
    #                                   blank=True, null=True,
    #                                   on_delete=models.SET_NULL,
    #                                   help_text=_('Материал корпуса'),
    #                                   verbose_name=_("Материал корпуса"))
    filter_element = models.ForeignKey(SilencerFilterElement, related_name='pneumaticsilencer_filter_element',
                                       blank=True, null=True,
                                       on_delete=models.SET_NULL,
                                       help_text=_('Фильтрующий элемент'),
                                       verbose_name=_("Фильтрующий элемент"))
    shape = models.ForeignKey(SilencerShape, related_name='pneumaticsilencer_shape',
                              blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Форма корпуса'),
                              verbose_name=_("Форма корпуса"))

    class Meta :
        ordering = ['brand' , 'code']
        verbose_name = _('Серия глушителей пневматических')
        verbose_name_plural = _('Серии глушителей пневматических')


class PneumaticSilencer(AbstractPneumaticFitting):
    """Глушитель пневматический (вид 'fitting-silencer')."""

    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'equipment_type', 'temperature_range',
        'thread', 'thread_inner_outer', 'pressure_range',
        'flow_rate', 'noise_level', 'operating_pressure',
        'body_material', 'pressure_min', 'pressure_max',
        'temp_min', 'temp_max', 'weight', 'width_across_flats',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name',
        'thread', 'thread_inner_outer', 'body_material', 'temperature_range',
        'pressure_range', 'flow_rate', 'noise_level', 'operating_pressure',
        'pressure_min', 'pressure_max', 'temp_min', 'temp_max',
        'weight', 'width_across_flats',
    )

    config_hash_fields = (
        'model_line', 'body_material', 'thread', 'thread_inner_outer',
        'flow_rate', 'noise_level', 'operating_pressure',
    )

    model_line = models.ForeignKey(PneumaticSilencerModelLine , related_name='pneumaticsilencer_items' ,
                                   blank=True , null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия') ,
                                   verbose_name=_("Серия"))
    flow_rate = models.DecimalField(
        max_digits=10 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Пропускная способность") ,
        help_text=_('Пропускная способность глушителя (Норм.л/мин)')
    )
    noise_level = models.DecimalField(
        max_digits=5 , decimal_places=1 , blank=True , null=True ,
        verbose_name=_("Уровень шума") ,
        help_text=_('Уровень шума глушителя (дБ)')
    )
    operating_pressure = models.DecimalField(
        max_digits=8 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Рабочее давление") ,
        help_text=_('Максимальное рабочее давление (бар)')
    )
    pressure_max = models.DecimalField(
        decimal_places=2 , max_digits=6 , null=True , blank=True ,
        verbose_name=_('P раб.макс (override), бар') ,
        help_text=_('Переопределение максимального давления для позиции. '
                    '0 или пусто — берётся значение серии.')
    )

    def _effective_pressure_max(self):
        """Максимальное давление глушителя: override позиции, иначе серия."""
        if self.pressure_max is not None and self.pressure_max != 0:
            return self.pressure_max
        ml = self.model_line
        return ml.pressure_max if ml else None

    class Meta :
        ordering = ['thread']
        verbose_name = _('Глушитель пневматический')
        verbose_name_plural = _('Глушители пневматические')
    FILTER_DEFINITIONS = _COMMON_FILTER_DEFINITIONS

    SEARCH_FIELDS = ['code']
    SELECT_RELATED_FIELDS = [
        'model_line__brand' , 'model_line' ,
        'body_material' , 'thread' , 'thread_inner_outer'
    ]

