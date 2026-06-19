# params/admin_signal.py
"""Админка для SignalRole, InputSignalSpec, ControlUnitSignalProfile и ControlUnitSignalProfileEntry."""
from django.contrib import admin
from django.db.models import Count
from core.models.mixins import AdminCopyMixin

from .signal_role import SignalRole
from .input_signal_spec import InputSignalSpec
from .control_unit_signal_profile import ControlUnitSignalProfile, ControlUnitSignalProfileEntry
from .actuator_heater_supply import ActuatorHeaterSupply
from django.utils.translation import gettext_lazy as _

class ControlUnitSignalProfileEntryInline(admin.TabularInline):
    model = ControlUnitSignalProfileEntry
    extra = 0
    fields = ['signal_role', 'sensor', 'input_signal', 'is_default_calibration']
    autocomplete_fields = ['signal_role', 'sensor', 'input_signal']
    ordering = ['signal_role__direction', 'signal_role__sorting_order']


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
class ControlUnitSignalProfileAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['name', 'code', 'entry_count', 'sorting_order', 'is_active']
    list_editable = ['code', 'sorting_order', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']
    inlines = [ControlUnitSignalProfileEntryInline]
    actions = ['copy_selected_objects']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_entry_count=Count('entries'))

    def entry_count(self, obj):
        return getattr(obj, '_entry_count', obj.entries.count())
    entry_count.short_description = "Записей"
    entry_count.admin_order_field = '_entry_count'

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'code', 'description')
        }),
        ('Отображение', {
            'fields': ('sorting_order', 'is_active')
        }),
    )


@admin.register(ActuatorHeaterSupply)
class ActuatorHeaterSupplyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'electrical_specs', 'sorting_order', 'is_active']
    list_editable = ['code', 'electrical_specs', 'sorting_order', 'is_active']
    search_fields = ['name', 'code', 'electrical_specs']
    ordering = ['sorting_order']

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'code', 'description')
        }),
        ('Электрика', {
            'fields': ('electrical_specs',)
        }),
        ('Отображение', {
            'fields': ('sorting_order', 'is_active')
        }),
    )