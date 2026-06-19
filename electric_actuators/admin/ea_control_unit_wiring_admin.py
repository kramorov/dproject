# electric_actuators/admin/ea_control_unit_wiring_admin.py
from django.contrib import admin

from core.models.mixins import AdminCopyMixin
from electric_actuators.models.ea_control_unit_wiring import ControlUnitWiring


@admin.register(ControlUnitWiring)
class ControlUnitWiringAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'control_unit', 'power_supply', 'signal_profile', 'heater_supply', 'is_active', 'sorting_order')
    list_filter = ('control_unit', 'power_supply', 'signal_profile', 'heater_supply', 'is_active')
    list_select_related = ('control_unit', 'power_supply', 'signal_profile', 'heater_supply')
    search_fields = ('code', 'name', 'control_unit__name', 'signal_profile__name')
    autocomplete_fields = ('control_unit', 'signal_profile')
    ordering = ('sorting_order', 'code')
    actions = ['copy_selected_objects']
    copy_suffix = ' (копия)'
