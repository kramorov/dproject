#electric_actuators/admin/ea_data_admin.py
from django.contrib import admin

from electric_actuators.models import ElectricActuatorData

def copy_electric_actuator_data(modeladmin, request, queryset):
    for obj in queryset:
        # Копируем объект
        obj.pk = None  # Убираем primary key, чтобы создать новый объект
        obj.name = obj.name + '(Копия)'
        obj.save()


copy_electric_actuator_data.short_description = "Копировать выбранные записи"

@admin.register(ElectricActuatorData)
class ElectricActuatorDataAdmin(admin.ModelAdmin):
    ordering = ['name', 'voltage', ]
    fieldsets = (
        ('Общая информация', {
            'fields': (
                ('name', 'model_line'), ('model_body', 'voltage'), ('time_to_open', 'time_to_open_measure_unit'),
                ('rotation_speed', 'rotation_speed_measure_unit'), ('torque_min', 'torque_max'), 'weight')
        }),
        ('Двигатель', {
            'fields': (
                ('motor_power', 'motor_power_measure_unit'),
                ('motor_current_rated', 'motor_current_rated_measure_unit'),
                ('motor_current_starting', 'motor_current_starting_measure_unit'))
        }),

    )
    list_display = ('name', 'model_line', 'model_body', 'voltage',)
    list_filter = ('name', 'model_line', 'voltage')
    actions = [copy_electric_actuator_data]  # Добавляем действие для копирования
