# params/admin_signal.py
"""Админка для SignalRole, ControlUnitSignalProfile и ControlUnitSignalProfileEntry."""
from django.contrib import admin

from .signal_role import SignalRole
from .control_unit_signal_profile import ControlUnitSignalProfile, ControlUnitSignalProfileEntry


class ControlUnitSignalProfileEntryInline(admin.TabularInline):
    model = ControlUnitSignalProfileEntry
    extra = 0
    fields = ['signal_role', 'sensor', 'is_default_calibration']
    autocomplete_fields = ['signal_role', 'sensor']


@admin.register(SignalRole)
class SignalRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_editable = ['code', 'sorting_order', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'code', 'description')
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
