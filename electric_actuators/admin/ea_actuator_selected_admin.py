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
    ElectricTemperatureOption , ElectricIpOption ,
    ElectricExdOption , ElectricBodyCoatingOption ,
    ElectricHandWheelOption
)


@admin.register(ElectricActuatorSelected)
class ElectricActuatorSelectedAdmin(admin.ModelAdmin) :
    list_display = [
        'name' ,
        'code' ,
        'selected_model_display' ,
        'is_active' ,

    ]

    list_filter = [
        'is_active' ,
        'selected_model_line_item' ,
    ]

    search_fields = [
        'name' ,
        'code' ,
        'description' ,

    ]

    fieldsets = (
        (None, {
            'fields': (
                ('selected_model_line_item', 'selected_power_supply'),
                ('name', 'code')
            )
        }),
        ('Опции', {
            'fields': (
                ('selected_temperature', 'selected_exd', 'selected_ip',),
                # ('selected_safety_position',),
                ('selected_hand_wheel', 'selected_control_unit_option'),
                ('selected_mechanical_indicator_option', 'selected_blinker_option'),
                ('selected_body_color_option','selected_body_coating'),
                ('selected_end_switches_option' , 'selected_way_switches_option' ,'selected_torque_switches_option' ,  ) ,
            )
        }),
        ('Монтажная площадка и кабельные вводы под заказ', {
            'fields': (
                ('actual_mounting_plate', 'actual_stem_shape', 'actual_stem_size'),
                'actual_cable_glands_holes',
            )
        }),
        ('Описание', {
            'fields': ('description',)  # обратите внимание на запятую
        })
    )

    class Media :
        js = ('admin/js/electric_actuator_selected_admin.js' ,)  # ИСПРАВЛЕНО имя файла

    def get_urls(self) :
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/generate-description/' ,
                self.admin_site.admin_view(self.generate_description_view) ,
                name='electric_actuator_generate_description'
            ) ,
            path(
                'get_options/' ,
                self.admin_site.admin_view(self.get_options_view) ,
                name='electric_actuator_get_options'
            ) ,
            path(
                'get_available_control_options/' ,  # УБЕДИТЕСЬ ЧТО ИМЯ ПРАВИЛЬНОЕ
                self.admin_site.admin_view(self.get_available_control_options_view) ,
                name='electric_actuator_get_available_control_options'
            ) ,
        ]
        return custom_urls + urls

    def get_available_control_options_view(self , request) :
        """API для получения доступных опций блоков управления для выбранного напряжения"""
        power_supply_id = request.GET.get('power_supply_id')
        print(f"=== get_available_control_options_view called ===")
        print(f"Power supply ID: {power_supply_id}")

        if not power_supply_id :
            print("No power supply ID provided")
            return JsonResponse({'options' : []})

        try :
            from electric_actuators.models.ea_model_line_item_options import ElectricControlUnitOption

            # Получаем опции блоков управления
            options = ElectricControlUnitOption.objects.filter(
                power_supply_option_id=power_supply_id ,
                is_active=True
            ).select_related('control_unit').order_by('sorting_order')

            options_list = []
            for option in options :
                options_list.append({
                    'id' : option.id ,
                    'control_unit_id' : option.control_unit.id ,
                    'control_unit_name' : str(option.control_unit) ,
                    'encoding' : option.encoding or '' ,
                    'is_default' : option.is_default ,
                    'description' : option.description or '' ,
                })

            print(f"Found {len(options_list)} control unit options")

            return JsonResponse({
                'success' : True ,
                'options' : options_list
            })

        except Exception as e :
            print(f"ERROR in get_available_control_options_view: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success' : False ,
                'error' : str(e) ,
                'options' : []
            } , status=500)

    def get_available_controls_view(self , request) :
        """API для получения доступных блоков управления для выбранного напряжения"""
        power_supply_id = request.GET.get('power_supply_id')
        print(f"=== get_available_controls_view called ===")
        print(f"Power supply ID: {power_supply_id}")

        if not power_supply_id :
            print("No power supply ID provided")
            return JsonResponse({'available_controls' : []})

        try :
            from electric_actuators.models.ea_model_line_item_options import ElectricPowerSupplyOption

            # Получаем опцию напряжения
            power_supply_option = ElectricPowerSupplyOption.objects.get(id=power_supply_id)
            print(f"Found power supply option: {power_supply_option}")

            # Получаем доступные блоки управления через ManyToMany
            available_controls = power_supply_option.control_unit_option.filter(
                is_active=True
            ).values_list('id' , flat=True)

            available_controls_list = list(available_controls)
            print(f"Available controls IDs: {available_controls_list}")

            return JsonResponse({
                'available_controls' : available_controls_list
            })

        except ElectricPowerSupplyOption.DoesNotExist :
            print(f"Power supply option with id {power_supply_id} not found")
            return JsonResponse({'error' : 'Power supply option not found'} , status=404)
        except Exception as e :
            print(f"ERROR in get_available_controls_view: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error' : str(e)} , status=500)

    def generate_description_view(self , request , object_id) :
        """View для генерации описания"""
        import traceback
        import logging
        logger = logging.getLogger(__name__)

        try :
            logger.info(f"Generate description called for object_id: {object_id}")

            # Получаем объект
            instance = self.get_object(request , object_id)
            logger.info(f"Instance found: {instance}")

            if not instance :
                logger.error(f"Object with id {object_id} not found")
                return JsonResponse({
                    'success' : False ,
                    'error' : 'Объект не найден' ,
                    'message' : 'Объект не найден'
                } , status=404)

            # Проверяем наличие метода
            logger.info(f"Checking methods for instance: {dir(instance)}")

            # Генерируем описание
            if hasattr(instance , '_generate_short_description') :
                logger.info("Calling _generate_short_description")
                description = instance._generate_short_description()
            else :
                logger.warning("Method _generate_short_description not found")
                description = f"Описание для {instance.name}"

            logger.info(f"Description generated, length: {len(description)}")

            return JsonResponse({
                'success' : True ,
                'description' : description ,
                'message' : 'Описание успешно сгенерировано'
            })

        except Exception as e :
            logger.error(f"Error in generate_description_view: {e}")
            logger.error(traceback.format_exc())

            return JsonResponse({
                'success' : False ,
                'error' : str(e) ,
                'message' : f'Ошибка при генерации описания: {str(e)}' ,
                'traceback' : traceback.format_exc()  # Только для разработки
            } , status=500)

    def get_options_view(self , request) :
        """API для получения опций через get_available_options"""
        model_id = request.GET.get('model_id')
        print(f"=== get_options_view called ===")
        print(f"Model ID: {model_id}")

        if not model_id :
            return JsonResponse({})

        try :
            from electric_actuators.models import ElectricActuatorModelLineItem

            model_item = ElectricActuatorModelLineItem.objects.get(id=model_id)
            print(f"Found model: {model_item.name}")

            # Создаем временный объект для вызова get_available_options
            temp_instance = self.model(
                selected_model_line_item=model_item
            )

            # Если есть power_supply_id в запросе, устанавливаем его
            power_supply_id = request.GET.get('power_supply_id')
            if power_supply_id :
                from electric_actuators.models.ea_model_line_item_options import ElectricPowerSupplyOption
                try :
                    power_supply = ElectricPowerSupplyOption.objects.get(id=power_supply_id)
                    temp_instance.selected_power_supply = power_supply
                    print(f"Set power supply: {power_supply}")
                except ElectricPowerSupplyOption.DoesNotExist :
                    print(f"Power supply with id {power_supply_id} not found")

            # Получаем опции через стандартный метод
            options = temp_instance.get_available_options()

            print(f"\n=== Options from get_available_options ===")
            for key , value in options.items() :
                print(f"{key}: {len(value)} items")
                if value and len(value) > 0 :
                    for i , opt in enumerate(value[:2]) :
                        print(f"  {i + 1}. id={opt['id']}, name='{opt['name']}'")

            return JsonResponse(options)

        except ElectricActuatorModelLineItem.DoesNotExist :
            print(f"Model with id {model_id} not found")
            return JsonResponse({'error' : 'Model not found'} , status=404)
        except Exception as e :
            print(f"ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error' : str(e)} , status=500)

    def selected_model_display(self , obj) :
        return obj.selected_model_line_item.name if obj.selected_model_line_item else "-"

    selected_model_display.short_description = "Модель"

    def temperature_display(self , obj) :
        return str(obj.selected_temperature) if obj.selected_temperature else "-"

    temperature_display.short_description = "Температура"

    def ip_display(self , obj) :
        return str(obj.selected_ip) if obj.selected_ip else "-"

    ip_display.short_description = "IP защита"

    def exd_display(self , obj) :
        return str(obj.selected_exd) if obj.selected_exd else "-"

    exd_display.short_description = "Взрывозащита"

    def body_coating_display(self , obj) :
        return str(obj.selected_body_coating) if obj.selected_body_coating else "-"

    body_coating_display.short_description = "Покрытие"

    def hand_wheel_display(self , obj) :
        return str(obj.selected_hand_wheel) if obj.selected_hand_wheel else "-"

    hand_wheel_display.short_description = "Ручной дублер"
