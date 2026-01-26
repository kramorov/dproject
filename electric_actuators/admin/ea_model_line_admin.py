#electric_actuators/admin/ea_model_line_admin.py

from django.contrib import admin

from electric_actuators.models import ModelLine


def copy_electric_actuator_data(modeladmin, request, queryset):
    for obj in queryset:
        # Копируем объект
        obj.pk = None  # Убираем primary key, чтобы создать новый объект
        obj.name = obj.name + '(Копия)'
        obj.save()


copy_electric_actuator_data.short_description = "Копировать выбранные записи"
@admin.register(ModelLine)
class ModelLineAdmin(admin.ModelAdmin):
    ordering = ['name']
    # Показать важные поля в списке объектов модели
    list_display = ('name', 'default_output_type', 'brand')

    fieldsets = (
        ('Общая информация', {
            'fields': (
                ('name', 'default_output_type', 'brand',), 'default_blinker')
        }),
        ('Опции', {
            'fields': (
                ('default_ip', 'allowed_ip'), ('default_exd', 'allowed_exd'),
                ('default_body_coating', 'allowed_body_coating'),
                ('default_temperature', 'allowed_temperature'),
                ('default_control_unit_installed', 'allowed_control_unit_installed'),)
        }),
        ('Конечные, путевые выключатели и датчики момента', {
            'fields': (
                ('default_end_switches', 'allowed_end_switches'), ('default_way_switches', 'allowed_way_switches'),
                ('default_torque_switches', 'allowed_torque_switches'))
        }),
        ('Прочее', {
            'fields': (
                ('default_hand_wheel', 'allowed_hand_wheel'), ('default_operating_mode', 'allowed_operating_mode'),
                )
        }),
    )

    actions = [copy_electric_actuator_data]  # Добавляем действие для копирования

