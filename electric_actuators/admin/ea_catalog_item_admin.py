# electric_actuators/admin/ea_catalog_item_admin.py
from django.contrib import admin

from electric_actuators.models.ea_catalog_item import ElectricActuatorCatalogItem


@admin.register(ElectricActuatorCatalogItem)
class ElectricActuatorCatalogItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'model_line', 'model_line_item',
                    'control_unit', 'mode', 'is_catalog', 'is_active')
    list_filter = ('is_catalog', 'is_active', 'model_line', 'control_unit')
    search_fields = ('code', 'name')
    autocomplete_fields = ('model_line', 'model_line_item', 'control_unit',
                           'power_supply')
    filter_horizontal = ('matrix_rows',)
    readonly_fields = ('config_hash',)
    ordering = ('model_line', 'code')
