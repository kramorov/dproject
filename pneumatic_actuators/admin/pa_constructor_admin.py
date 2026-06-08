# pneumatic_actuators/admin/pa_constructor_admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db import models

from pneumatic_actuators.models.pa_actuator_constructor import PneumaticActuatorConstructor


@admin.register(PneumaticActuatorConstructor)
class PneumaticActuatorConstructorAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'required': False},
    }

    list_display = [
        'name', 'code', 'selected_model_display',
        'safety_position_display', 'springs_qty_display',
        'temperature_display', 'ip_display', 'exd_display',
        'body_coating_display', 'hand_wheel_display',
        'sorting_order', 'is_active',
        'description_preview',
    ]
    list_filter = [
        'is_active', 'selected_model_line', 'selected_model_line_item',
    ]
    search_fields = ['name', 'code']
    autocomplete_fields = ['selected_model_line_item', 'selected_model_line']

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'selected_model_line', 'selected_model_line_item',
                'name', 'code',
            )
        }),
        ('Опции привода', {
            'fields': (
                ('selected_safety_position', 'selected_springs_qty', 'selected_temperature'),
                ('selected_ip', 'selected_exd', 'selected_body_coating', 'selected_hand_wheel'),
            ),
        }),
        ('Температура', {
            'fields': (('work_temp_min', 'work_temp_max'),),
        }),
        ('Служебное', {
            'fields': ('description', 'sorting_order', 'is_active', 'is_unique'),
        }),
    )

    readonly_fields = ['name', 'code', 'is_unique']

    # --- display helpers ---
    def selected_model_display(self, obj):
        return str(obj.selected_model_line_item) if obj.selected_model_line_item else "-"
    selected_model_display.short_description = "Модель"

    def safety_position_display(self, obj):
        return str(obj.selected_safety_position) if obj.selected_safety_position else "-"
    safety_position_display.short_description = "Положение безоп."

    def springs_qty_display(self, obj):
        return str(obj.selected_springs_qty) if obj.selected_springs_qty else "-"
    springs_qty_display.short_description = "Пружины"

    def temperature_display(self, obj):
        return str(obj.selected_temperature) if obj.selected_temperature else "-"
    temperature_display.short_description = "Температура"

    def ip_display(self, obj):
        return str(obj.selected_ip) if obj.selected_ip else "-"
    ip_display.short_description = "IP"

    def exd_display(self, obj):
        return str(obj.selected_exd) if obj.selected_exd else "-"
    exd_display.short_description = "Exd"

    def body_coating_display(self, obj):
        return str(obj.selected_body_coating) if obj.selected_body_coating else "-"
    body_coating_display.short_description = "Покрытие"

    def hand_wheel_display(self, obj):
        return str(obj.selected_hand_wheel) if obj.selected_hand_wheel else "-"
    hand_wheel_display.short_description = "Дублер"

    def description_preview(self, obj):
        if not obj.pk:
            return "—"
        desc = obj.description or obj._generate_short_description()
        return format_html(
            '<pre style="white-space: pre-wrap; max-height: 120px; overflow-y: auto; '
            'font-size: 11px; margin: 0;">{}</pre>',
            desc[:500]
        )
    description_preview.short_description = "Описание"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'selected_model_line',
            'selected_model_line_item',
            'selected_safety_position',
            'selected_springs_qty',
            'selected_temperature',
            'selected_ip',
            'selected_exd',
            'selected_body_coating',
            'selected_hand_wheel',
        )
