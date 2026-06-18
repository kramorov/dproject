# params/admin_signal.py
"""Админка для SignalRole, InputSignalSpec, ControlUnitSignalProfile и ControlUnitSignalProfileEntry."""
from django.contrib import admin
from core.models.mixins import AdminCopyMixin

from .signal_role import SignalRole
from .input_signal_spec import InputSignalSpec
from .control_unit_signal_profile import ControlUnitSignalProfile, ControlUnitSignalProfileEntry
from django.utils.translation import gettext_lazy as _

class ControlUnitSignalProfileEntryInline(admin.TabularInline):
    model = ControlUnitSignalProfileEntry
    extra = 0
    fields = ['signal_role', 'sensor', 'input_signal', 'is_default_calibration']
    autocomplete_fields = ['signal_role', 'sensor', 'input_signal']


@admin.register(SignalRole)
class SignalRoleAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['name', 'code', 'direction', 'sorting_order', 'is_active']
    list_editable = ['code', 'sorting_order', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']
    actions = ['copy_selected_objects', 'delete_selected']

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'code', 'description')
        }),
        ('Отображение', {
            'fields': ('sorting_order', 'is_active')
        }),
        ('Направление', {
            'fields': ('direction',),
            'description': _('Входной — команда приводу, выходной — обратная связь')
        }),
    )


@admin.register(InputSignalSpec)
class InputSignalSpecAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'signal_category', 'electrical_specs', 'sorting_order', 'is_active']
    list_editable = ['code', 'signal_category', 'sorting_order', 'is_active']
    list_filter = ['signal_category', 'is_active']
    search_fields = ['name', 'code', 'electrical_specs']
    ordering = ['sorting_order']

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'code', 'signal_category', 'description')
        }),
        ('Электрика', {
            'fields': ('electrical_specs', 'wires_count')
        }),
        ('Отображение', {
            'fields': ('sorting_order', 'is_active')
        }),
    )


@admin.register(ControlUnitSignalProfile)
class ControlUnitSignalProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'entry_count', 'sorting_order', 'is_active']
    list_editable = ['code', 'sorting_order', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']
    inlines = [ControlUnitSignalProfileEntryInline]

    def entry_count(self, obj):
        return obj.entries.count()
    entry_count.short_description = "Записей"

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'code', 'description')
        }),
        ('Отображение', {
            'fields': ('sorting_order', 'is_active')
        }),
    )