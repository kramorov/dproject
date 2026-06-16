# params/admin_feedback.py
"""Админка для FeedbackSignalSet."""
from django.contrib import admin

from .feedback_signals import FeedbackSignalSet


@admin.register(FeedbackSignalSet)
class FeedbackSignalSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sensor_count', 'sorting_order', 'is_active']
    list_editable = ['code', 'sorting_order', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']
    filter_horizontal = ['sensors']

    def sensor_count(self, obj):
        return obj.sensors.count()
    sensor_count.short_description = "Датчиков"

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'code', 'description')
        }),
        ('Датчики в наборе', {
            'fields': ('sensors',),
            'description': (
                'Выберите конкретные датчики из базы pa_controls. '
                'Каждый датчик уже содержит тип сигнала, форму контакта и состояние.'
            )
        }),
        ('Отображение', {
            'fields': ('sorting_order', 'is_active')
        }),
    )
