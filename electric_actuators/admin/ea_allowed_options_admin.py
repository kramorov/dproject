# electric_actuators/admin/ea_allowed_options_admin.py
"""Админка для AllowedControlUnitOption, AllowedTurnCounterOption, AllowedSignalProfileOption."""
from django.contrib import admin

from electric_actuators.models.ea_allowed_options import (
    AllowedControlUnitOption,
    AllowedTurnCounterOption,
    AllowedSignalProfileOption,
)


@admin.register(AllowedControlUnitOption)
class AllowedControlUnitOptionAdmin(admin.ModelAdmin):
    list_display = ['model_line', 'control_unit', 'encoding', 'is_active', 'sorting_order']
    list_editable = ['encoding', 'is_active', 'sorting_order']
    list_filter = ['model_line', 'is_active']
    search_fields = ['model_line__name', 'control_unit__name', 'encoding']
    autocomplete_fields = ['model_line', 'control_unit']


@admin.register(AllowedTurnCounterOption)
class AllowedTurnCounterOptionAdmin(admin.ModelAdmin):
    list_display = ['model_line', 'turn_counter', 'encoding', 'is_active', 'sorting_order']
    list_editable = ['encoding', 'is_active', 'sorting_order']
    list_filter = ['model_line', 'is_active']
    search_fields = ['model_line__name', 'turn_counter__name', 'encoding']
    autocomplete_fields = ['model_line', 'turn_counter']


@admin.register(AllowedSignalProfileOption)
class AllowedSignalProfileOptionAdmin(admin.ModelAdmin):
    list_display = ['model_line', 'signal_profile', 'encoding', 'is_active', 'sorting_order']
    list_editable = ['encoding', 'is_active', 'sorting_order']
    list_filter = ['model_line', 'is_active']
    search_fields = ['model_line__name', 'signal_profile__name', 'encoding']
    autocomplete_fields = ['model_line', 'signal_profile']
