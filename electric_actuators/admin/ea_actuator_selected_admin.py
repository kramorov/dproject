# electric_actuators/admin/ea_actuator_selected_admin.py

from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from django.db import models
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError

from electric_actuators.models.ea_actuator_selected import ElectricActuatorSelected
from electric_actuators.models.ea_options import (
    ElectricTemperatureOption, ElectricIpOption,
    ElectricExdOption, ElectricBodyCoatingOption,
    ElectricHandWheelOption
)


@admin.register(ElectricActuatorSelected)
class ElectricActuatorSelectedAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'selected_model_display', 'is_active']
    list_filter = ['is_active', 'selected_model_line_item']
    search_fields = ['name', 'code', 'description']

    autocomplete_fields = ['selected_model_line_item']

    # Простые fieldsets без лишних полей
    fieldsets = (
        (None, {
            'fields': ('selected_model_line_item', ('name', 'code'))
        }),
        ('Опции', {
            'fields': (
                ('selected_temperature',
                'selected_ip'),
                ('selected_exd',
                'selected_body_coating'),
                'selected_hand_wheel', 'selected_power_supply',
            )
        }),
        ('Конструкция', {
            'fields': (
                'actual_mounting_plate',
                'actual_stem_shape',
                'actual_stem_size',
                'actual_cable_glands_holes',
            )
        }),
        ('Описание', {
            'fields': ('description',)
        })
    )

    class Media:
        js = ('admin/js/electric_actuator_selected_admin.js',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/generate-description/',
                self.admin_site.admin_view(self.generate_description_view),
                name='electric_actuator_generate_description'
            ),
            path(
                'get_options/',
                self.admin_site.admin_view(self.get_options_view),
                name='electric_actuator_get_options'
            ),
        ]
        return custom_urls + urls

    def generate_description_view(self, request, object_id):
        """View для генерации описания"""
        try:
            instance = self.get_object(request, object_id)

            # Генерируем описание
            if hasattr(instance, '_generate_short_description'):
                description = instance._generate_short_description()
            else:
                description = f"Описание для {instance.name}"

            return JsonResponse({
                'success': True,
                'description': description,
                'message': 'Описание успешно сгенерировано'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Ошибка при генерации описания'
            }, status=500)

    def get_options_view(self, request):
        """API для получения опций через get_available_options"""
        model_id = request.GET.get('model_id')
        print(f"=== get_options_view called ===")
        print(f"Model ID: {model_id}")

        if not model_id:
            return JsonResponse({})

        try:
            from electric_actuators.models import ElectricActuatorModelLineItem

            model_item = ElectricActuatorModelLineItem.objects.get(id=model_id)
            print(f"Found model: {model_item.name}")

            # Создаем временный объект для вызова get_available_options
            temp_instance = self.model(
                selected_model_line_item=model_item
            )

            # Получаем опции через стандартный метод
            options = temp_instance.get_available_options()

            print(f"\n=== Options from get_available_options ===")
            for key, value in options.items():
                print(f"{key}: {len(value)} items")
                if value and len(value) > 0:
                    for i, opt in enumerate(value[:2]):
                        print(f"  {i + 1}. id={opt['id']}, name='{opt['name']}'")

            return JsonResponse(options)

        except ElectricActuatorModelLineItem.DoesNotExist:
            print(f"Model with id {model_id} not found")
            return JsonResponse({'error': 'Model not found'}, status=404)
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    def selected_model_display(self, obj):
        return obj.selected_model_line_item.name if obj.selected_model_line_item else "-"

    selected_model_display.short_description = "Модель"

    def temperature_display(self, obj):
        return str(obj.selected_temperature) if obj.selected_temperature else "-"

    temperature_display.short_description = "Температура"

    def ip_display(self, obj):
        return str(obj.selected_ip) if obj.selected_ip else "-"

    ip_display.short_description = "IP защита"

    def exd_display(self, obj):
        return str(obj.selected_exd) if obj.selected_exd else "-"

    exd_display.short_description = "Взрывозащита"

    def body_coating_display(self, obj):
        return str(obj.selected_body_coating) if obj.selected_body_coating else "-"

    body_coating_display.short_description = "Покрытие"

    def hand_wheel_display(self, obj):
        return str(obj.selected_hand_wheel) if obj.selected_hand_wheel else "-"

    hand_wheel_display.short_description = "Ручной дублер"