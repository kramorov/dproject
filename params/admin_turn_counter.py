# params/admin_turn_counter.py
"""Админка для TurnCounterOption."""
from django.contrib import admin

from .turn_counter import TurnCounterOption


@admin.register(TurnCounterOption)
class TurnCounterOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'counter_type', 'max_turns', 'sorting_order', 'is_active']
    list_editable = ['code', 'counter_type', 'max_turns', 'sorting_order', 'is_active']
    list_filter = ['counter_type', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'code', 'description')
        }),
        ('Параметры', {
            'fields': ('counter_type', 'max_turns')
        }),
        ('Отображение', {
            'fields': ('sorting_order', 'is_active')
        }),
    )
