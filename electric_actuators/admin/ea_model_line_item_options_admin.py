# electric_actuators/admin/ea_model_line_item_options_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html

from electric_actuators.models.ea_model_line_item_options import ElectricPowerSupplyOption
from params.admin import PowerSuppliesAdmin  # если нужно автодополнение


def copy_electric_power_supply_option(modeladmin , request , queryset) :
    """Копировать выбранные опции питания с добавлением '(Копия)'"""
    copied_count = 0
    errors = []

    for obj in queryset :
        try :
            # Создаем копию объекта
            copy_obj = ElectricPowerSupplyOption()

            # Копируем все поля кроме id
            for field in obj._meta.fields :
                if field.name not in ['id' , 'pk'] :
                    setattr(copy_obj , field.name , getattr(obj , field.name))

            # Добавляем "(Копия)" к названию и кодировке
            if hasattr(copy_obj , 'name') and copy_obj.name :
                copy_obj.name = f"{copy_obj.name} (Копия)"

            if hasattr(copy_obj , 'encoding') and copy_obj.encoding :
                copy_obj.encoding = f"{copy_obj.encoding} (Копия)"
            elif hasattr(copy_obj , 'encoding') :
                copy_obj.encoding = "copy"

            copy_obj.save()
            copied_count += 1

        except Exception as e :
            errors.append(f"{obj}: {str(e)}")

    # Показываем результат
    if copied_count > 0 :
        modeladmin.message_user(
            request ,
            f"Успешно скопировано {copied_count} опций питания" ,
            messages.SUCCESS
        )

    if errors :
        modeladmin.message_user(
            request ,
            f"Ошибки при копировании: {', '.join(errors[:5])}" +
            ("..." if len(errors) > 5 else "") ,
            messages.ERROR
        )


copy_electric_power_supply_option.short_description = "📋 Копировать выбранные опции питания"


@admin.register(ElectricPowerSupplyOption)
class ElectricPowerSupplyOptionAdmin(admin.ModelAdmin) :
    """Админка для опций напряжения питания модели в серии электроприводов"""

    list_display = (
        'model_line_item_display' ,
        'power_supply_display' ,
        'encoding_display' ,
        'torque_range' ,
        'time_to_open' ,
        'rotation_speed' ,
        'is_active' ,
        'sorting_order' ,
    )

    list_editable = (
        'is_active' ,
        'sorting_order' ,
    )

    list_filter = (
        'is_active' ,
        'power_supply' ,
        'model_line_item__model_line' ,
    )

    # search_fields = (
    #     'encoding' ,
    #     'description' ,
    #     'model_line_item__name' ,
    #     'model_line_item__code' ,
    #     'model_line_item__model_line__name' ,
    #     'power_supply__name' ,
    #     'power_supply__code' ,
    # )

    ordering = ('model_line_item' , 'sorting_order')

    actions = [copy_electric_power_supply_option]

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                ('model_line_item' , 'power_supply', 'encoding' ,) ,
                ('is_active' , 'sorting_order') ,
            )
        }) ,
        (_('Электрические параметры') , {
            'fields' : (
                ('motor_current_rated' , 'motor_current_starting') ,
                'motor_power' ,
            )
        }) ,
        (_('Механические параметры') , {
            'fields' : (
                ('torque_min' , 'torque_max') ,
                ('time_to_open' , 'rotation_speed') ,
            )
        }) ,
    )

    raw_id_fields = ['model_line_item' , 'power_supply']

    # Автодополнение для ForeignKey полей
    # autocomplete_fields = ['power_supply']

    # Методы для отображения в списке
    def model_line_item_display(self , obj) :
        """Отображение модели в серии"""
        if obj.model_line_item :
            return format_html(
                '<strong>{}</strong><br><small>Серия: {}</small>' ,
                obj.model_line_item.name ,
                obj.model_line_item.model_line.name if obj.model_line_item.model_line else '-'
            )
        return "-"

    model_line_item_display.short_description = _('Модель')
    model_line_item_display.admin_order_field = 'model_line_item__name'

    def power_supply_display(self , obj) :
        """Отображение напряжения питания"""
        if obj.power_supply :
            return format_html(
                '{}<br><small>{}</small>' ,
                obj.power_supply.name ,
                obj.power_supply.voltage if hasattr(obj.power_supply , 'voltage') else ''
            )
        return "-"

    power_supply_display.short_description = _('Напряжение питания')
    power_supply_display.admin_order_field = 'power_supply__name'

    def encoding_display(self , obj) :
        """Отображение кодировки с подсветкой"""
        if obj.encoding :
            if obj.is_default :
                return format_html(
                    '<span style="background-color: #d4edda; padding: 2px 6px; border-radius: 3px;">'
                    '{} (стандарт)</span>' ,
                    obj.encoding
                )
            return obj.encoding
        return "-"

    encoding_display.short_description = _('Кодировка')

    def torque_range(self , obj) :
        """Отображение диапазона усилия"""
        if obj.torque_min and obj.torque_max :
            return f"{obj.torque_min}...{obj.torque_max} Нм"
        elif obj.torque_min :
            return f"от {obj.torque_min} Нм"
        elif obj.torque_max :
            return f"до {obj.torque_max} Нм"
        return "-"

    torque_range.short_description = _('Усилие, Нм')

    # Оптимизация запросов
    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'model_line_item' ,
            'model_line_item__model_line' ,
            'power_supply'
        )

    # Проверка уникальности дефолтных опций
    def save_model(self , request , obj , form , change) :
        super().save_model(request , obj , form , change)



    # Фильтр по серии
    # def get_list_filter(self , request) :
    #     list_filter = list(self.list_filter)
    #
    #     return tuple(list_filter)

    # # Кнопка быстрого копирования на странице редактирования
    # def change_view(self , request , object_id , form_url='' , extra_context=None) :
    #     extra_context = extra_context or {}
    #     extra_context['show_copy_button'] = True
    #     return super().change_view(request , object_id , form_url , extra_context)
    #
    # def response_change(self , request , obj) :
    #     if "_copy_this" in request.POST :
    #         # Копируем текущий объект
    #         try :
    #             new_obj = ElectricPowerSupplyOption()
    #
    #             for field in obj._meta.fields :
    #                 if field.name not in ['id' , 'pk'] :
    #                     setattr(new_obj , field.name , getattr(obj , field.name))
    #
    #             if hasattr(new_obj , 'encoding') and new_obj.encoding :
    #                 new_obj.encoding = f"{new_obj.encoding}_copy"
    #             elif hasattr(new_obj , 'encoding') :
    #                 new_obj.encoding = "copy"
    #
    #             if hasattr(new_obj , 'is_default') :
    #                 new_obj.is_default = False
    #
    #             if hasattr(new_obj , 'sorting_order') :
    #                 new_obj.sorting_order = (obj.sorting_order or 0) + 1000
    #
    #             new_obj.save()
    #
    #             self.message_user(
    #                 request ,
    #                 f"Опция питания успешно скопирована (новая запись: {new_obj.pk})" ,
    #                 messages.SUCCESS
    #             )
    #
    #             # Перенаправляем на редактирование копии
    #             from django.urls import reverse
    #             from django.http import HttpResponseRedirect
    #             return HttpResponseRedirect(
    #                 reverse('admin:electric_actuators_electricpowersupplyoption_change' , args=[new_obj.pk])
    #             )
    #
    #         except Exception as e :
    #             self.message_user(
    #                 request ,
    #                 f"Ошибка при копировании: {str(e)}" ,
    #                 messages.ERROR
    #             )
    #
    #     return super().response_change(request , obj)