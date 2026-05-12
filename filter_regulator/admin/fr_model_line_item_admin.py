#filter_requlator/admin/fr_model_line_item_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminCopyMixin
from filter_regulator.models import FilterRegulator


@admin.register(FilterRegulator)
class FilterRegulatorAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ('name', 'code', 'model_line',  'gauge_quantity', 'sorting_order', 'is_active', )
    list_filter = ('is_active', 'model_line', 'drain_variety', 'gauge_quantity', )
    list_editable = ( 'code', 'model_line','is_active', 'sorting_order')
    search_fields = ('name', 'code', 'model_line__name',)
    ordering = ('sorting_order', 'name')


    fieldsets = (
        (None, {
            'fields': ( ('code', 'model_line', 'body'),'description',  ('drain_variety','filter_element_material'), ('is_active', 'sorting_order'),)
        }),
        (_('Характеристики'), {
            'fields': ( ('filtration_rating',   'flow_rate'), ('gauge_quantity','wall_mounting_included', 'has_shut_off_valve'),)
        }),
        (_('Рабочие параметры'), {
            'fields': (('work_temp_min', 'work_temp_max'), ('pressure_min', 'pressure_max', 'pressure_inlet_max'))
        }),
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
            'description': _('JSON формат: {"key": "value"}')
        }),
    )
    actions = ['copy_selected_objects']