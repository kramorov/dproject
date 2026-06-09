# electric_actuators/admin/ea_constructor_admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db import models

from electric_actuators.models.ea_actuator_constructor import ElectricActuatorConstructor


@admin.register(ElectricActuatorConstructor)
class ElectricActuatorConstructorAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'required': False},
    }

    list_display = [
        'name', 'code', 'selected_model_display',
        'power_supply_display', 'safety_position_display',
        'temperature_display', 'ip_display', 'exd_display',
        'body_coating_display', 'body_color_display', 'hand_wheel_display',
        'turn_angle_display', 'blinker_display', 'mechanical_indicator_display',
        'sorting_order', 'is_active',
        'description_preview',
    ]
    list_filter = [
        'is_active', 'selected_model_line', 'selected_model_line_item',
        'selected_power_supply',
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
        ('Напряжение и управление', {
            'fields': (
                'selected_power_supply',
                ('selected_safety_position', 'selected_control_unit_option'),
            ),
        }),
        ('Климат и защита', {
            'fields': (
                ('selected_temperature', 'selected_ip', 'selected_exd'),
            ),
        }),
        ('Корпус', {
            'fields': (
                ('selected_body_coating', 'selected_body_color_option', 'selected_hand_wheel'),
                ('selected_turn_angle_option', 'selected_cable_glands_holes'),
            ),
        }),
        ('Индикация', {
            'fields': (
                ('selected_blinker_option', 'selected_mechanical_indicator_option'),
            ),
        }),
        ('Выключатели', {
            'fields': (
                ('selected_end_switches_option', 'selected_way_switches_option', 'selected_torque_switches_option'),
            ),
        }),
        ('Присоединение к арматуре', {
            'fields': (
                ('actual_mounting_plate', 'actual_stem_shape', 'actual_stem_size'),
                'actual_cable_glands_holes',
            ),
        }),
        ('Температура (расчётная)', {
            'fields': (('work_temp_min', 'work_temp_max'),),
        }),
        ('Служебное', {
            'fields': ('description', 'sorting_order', 'is_active', 'is_unique'),
        }),
    )

    readonly_fields = ['name', 'code', 'is_unique', 'work_temp_min', 'work_temp_max']

    # --- display helpers ---
    def selected_model_display(self, obj):
        return str(obj.selected_model_line_item) if obj.selected_model_line_item else "-"
    selected_model_display.short_description = "Модель"

    def power_supply_display(self, obj):
        return str(obj.selected_power_supply) if obj.selected_power_supply else "-"
    power_supply_display.short_description = "Напряжение"

    def safety_position_display(self, obj):
        return str(obj.selected_safety_position) if obj.selected_safety_position else "-"
    safety_position_display.short_description = "Безоп. положение"

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

    def body_color_display(self, obj):
        return str(obj.selected_body_color_option) if obj.selected_body_color_option else "-"
    body_color_display.short_description = "Цвет"

    def hand_wheel_display(self, obj):
        return str(obj.selected_hand_wheel) if obj.selected_hand_wheel else "-"
    hand_wheel_display.short_description = "Дублер"

    def turn_angle_display(self, obj):
        return str(obj.selected_turn_angle_option) if obj.selected_turn_angle_option else "-"
    turn_angle_display.short_description = "Угол"

    def blinker_display(self, obj):
        return str(obj.selected_blinker_option) if obj.selected_blinker_option else "-"
    blinker_display.short_description = "Блинкер"

    def mechanical_indicator_display(self, obj):
        return str(obj.selected_mechanical_indicator_option) if obj.selected_mechanical_indicator_option else "-"
    mechanical_indicator_display.short_description = "Мех. инд."

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
            'selected_power_supply',
            'selected_safety_position',
            'selected_control_unit_option',
            'selected_temperature',
            'selected_ip',
            'selected_exd',
            'selected_body_coating',
            'selected_body_color_option',
            'selected_hand_wheel',
            'selected_turn_angle_option',
            'selected_blinker_option',
            'selected_mechanical_indicator_option',
            'selected_cable_glands_holes',
            'selected_end_switches_option',
            'selected_way_switches_option',
            'selected_torque_switches_option',
            'actual_mounting_plate',
            'actual_stem_shape',
            'actual_stem_size',
            'actual_cable_glands_holes',
        )
