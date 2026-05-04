#filter_requlator/admin/fr_model_line_item_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from filter_regulator.models import FilterRegulator


@admin.register(FilterRegulator)
class FilterRegulatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'model_line', 'filter_variety', 'gauge_quantity', 'is_active', 'sorting_order')
    list_filter = ('is_active', 'model_line', 'filter_variety', 'drain_variety', 'gauge_quantity', )
    search_fields = ('name', 'code', 'model_line__name', 'filter_variety__name')
    ordering = ('sorting_order', 'name')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'model_line', 'filter_variety', 'body', 'drain_variety', 'is_active', 'sorting_order')
        }),
        (_('Характеристики'), {
            'fields': ('gauge_quantity', 'filtration_rating', 'filter_element_material',  'flow_rate', 'wall_mounting_included', 'has_shut_off_valve')
        }),
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
            'description': _('JSON формат: {"key": "value"}')
        }),
    )