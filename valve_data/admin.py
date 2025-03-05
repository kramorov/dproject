from django.contrib import admin
from django.db import models
from valve_data.models import ValveLine, ValveModelData


def duplicate_selected_action(model_admin, request, queryset):
    for obj in queryset:
        # Создаем копию объекта с обнулением pk
        # Create a new instance and copy field values (excluding the pk)
        # Object Copying: Instead of using obj.copy(), I manually create a new instance of the same class
        # (obj.__class__()) and copy the values from the original object to the new one.
        new_obj = obj.__class__()
        # Copy the field values from the original object to the new object
        for field in obj._meta.fields:
            if field.name != 'id':  # Exclude the primary key field
                setattr(new_obj, field.name, getattr(obj, field.name))

        # Проверяем, есть ли поле symbolic_code и добавляем 'K', если есть
        if hasattr(obj, 'symbolic_code') and isinstance(obj._meta.get_field('symbolic_code'), models.CharField):
            new_obj.symbolic_code = f"{new_obj.symbolic_code}(K"  # Добавляем 'K' в конец

        # Обнуляем pk для новой записи
        new_obj.pk = None
        new_obj.save()  # Сохраняем новый объект

        # Копируем ManyToMany связи для ett_doc
        if hasattr(obj, 'valve_model_mounting_plate') and isinstance(obj._meta.get_field('valve_model_mounting_plate'), models.ManyToManyField):
            for mounting_plate in obj.valve_model_mounting_plate.all():
                new_obj.valve_model_mounting_plate.add(mounting_plate)

    model_admin.message_user(request, "Выбранные записи успешно скопированы.")


class ValveDataValveLineAdmin(admin.ModelAdmin):
    list_display = ('symbolic_code', 'valve_type', 'valve_producer', 'valve_brand')  # Отображаем нужные поля
    actions = [duplicate_selected_action]  # Кнопка копирования


class ValveDataValveModelDataAdmin(admin.ModelAdmin):
    ordering = ['symbolic_code', 'valve_model_dn', 'valve_model_pn']
    fieldsets = (
        ('Модель', {
            'fields': (
                ('symbolic_code', 'valve_type', 'valve_model_model_line'),
            )
        }),
        ('Давление', {
            'fields': (
                ('valve_model_dn', 'valve_model_pn', 'valve_model_pn_delta'),
                ('valve_model_pn_measure_unit', 'valve_model_pn_delta_measure_unit',))
        }),
        ('Усилие, обороты', {
            'fields': (
                ('valve_model_torque_to_close', 'valve_model_torque_to_open', 'valve_model_rotations_to_open'))
        }),
        ('Монтажная площадка и шток', {
            'fields': (
                ('valve_model_mounting_plate', 'valve_model_stem_size',))
        }),
    )
    list_display = (
    'symbolic_code', 'valve_model_dn', 'valve_model_pn', 'valve_model_torque_to_close', 'valve_model_torque_to_open', 'valve_model_rotations_to_open', 'valve_model_model_line')  # Отображаем нужные поля
    list_filter = ('valve_model_model_line', 'valve_model_pn',)
    actions = [duplicate_selected_action]  # Кнопка копирования


admin.site.register(ValveLine, ValveDataValveLineAdmin)
admin.site.register(ValveModelData, ValveDataValveModelDataAdmin)
