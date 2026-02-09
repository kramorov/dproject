# electric_actuators/admin/ea_model_line_item_options_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html

from electric_actuators.models.ea_model_line_item_options import ElectricPowerSupplyOption


def copy_electric_power_supply_option(modeladmin, request, queryset):
    """Копировать выбранные опции питания с использованием create_copy() метода"""
    from django.contrib import messages

    copied_count = 0
    errors = []
    copied_items = []

    for obj in queryset:
        try:
            # Проверяем, есть ли у объекта метод create_copy
            if not hasattr(obj, 'create_copy') or not callable(getattr(obj, 'create_copy')):
                errors.append(f"{obj}: Объект не имеет метода create_copy()")
                continue

            # Используем метод create_copy из модели
            copy_obj = obj.create_copy()

            # Добавляем "(Копия)" к полям если нужно
            if hasattr(copy_obj, 'name') and copy_obj.name:
                original_name = copy_obj.name
                copy_obj.name = f"{original_name} (Копия)"
                copy_obj.save()
                copied_items.append(f"{original_name} → {copy_obj.name}")
            else:
                copied_items.append(f"ID: {obj.id} → ID: {copy_obj.id}")

            copied_count += 1

        except Exception as e:
            error_msg = f"{obj}: {str(e)}"
            errors.append(error_msg)

    # Формируем детальное сообщение
    if copied_count > 0:
        message = f"Успешно скопировано {copied_count} опций питания:\n"
        for i, item in enumerate(copied_items[:5]):  # Показываем первые 5
            message += f"\n{i + 1}. {item}"

        if len(copied_items) > 5:
            message += f"\n... и ещё {len(copied_items) - 5} опций"

        modeladmin.message_user(request, message, messages.SUCCESS)

    if errors:
        error_message = f"Ошибки при копировании {len(errors)} опций:"
        for i, error in enumerate(errors[:3]):
            error_message += f"\n{i + 1}. {error}"

        if len(errors) > 3:
            error_message += f"\n... и ещё {len(errors) - 3} ошибок"

        modeladmin.message_user(request, error_message, messages.WARNING)

    # Итоговое сообщение
    if copied_count > 0 or errors:
        modeladmin.message_user(
            request,
            f"Итог: {copied_count} успешно, {len(errors)} с ошибками",
            messages.INFO
        )


copy_electric_power_supply_option.short_description = "📋 Копировать выбранные опции питания"


@admin.register(ElectricPowerSupplyOption)
class ElectricPowerSupplyOptionAdmin(admin.ModelAdmin):
    list_display = ('model_line_item', 'power_supply', 'get_time_open',
                    'get_time_close', 'get_torque_range', 'display_control_units')
    list_filter = ('model_line_item', 'power_supply', 'control_unit_option', 'is_active')
    search_fields = ('model_line_item__name', 'power_supply__name', 'encoding')
    ordering = ('model_line_item', 'sorting_order')

    # Горизонтальный выбор для ManyToMany
    filter_horizontal = ('control_unit_option',)

    # Используем TabbedInline для группировки полей по вкладкам
    fieldsets = (
        (None, {
            'fields': (
                'model_line_item',
                'power_supply',
                'control_unit_option',
                'is_active',
                'sorting_order'
            )
        }),
        (_('Кодирование'), {
            'fields': ('encoding',),
            'classes': ('collapse',)
        }),
        (_('Характеристики двигателя'), {
            'fields': (
                'motor_current_rated',
                'motor_current_starting',
                'motor_power'
            )
        }),
        (_('Характеристики работы'), {
            'fields': (
                'time_to_open',
                'time_to_close',
                'torque_min',
                'torque_max'
            )
        }),
        (_('Описание'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    # Добавляем кастомные методы для отображения в списке
    def get_time_open(self, obj):
        return f"{obj.time_to_open} с" if obj.time_to_open else "-"

    get_time_open.short_description = _('Время открытия')
    get_time_open.admin_order_field = 'time_to_open'

    def get_time_close(self, obj):
        return f"{obj.time_to_close} с" if obj.time_to_close else "-"

    get_time_close.short_description = _('Время закрытия')
    get_time_close.admin_order_field = 'time_to_close'

    def get_torque_range(self, obj):
        if obj.torque_min and obj.torque_max:
            return f"{obj.torque_min}-{obj.torque_max} Нм"
        elif obj.torque_min:
            return f"от {obj.torque_min} Нм"
        elif obj.torque_max:
            return f"до {obj.torque_max} Нм"
        return "-"

    get_torque_range.short_description = _('Диапазон усилия')

    def display_control_units(self, obj):
        count = obj.control_unit_option.count()
        if count > 0:
            return f"{count} шт."
        return "-"

    display_control_units.short_description = _('Блоки упр.')

    # Настройка формы для редактирования
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "control_unit_option":
            # Можно добавить фильтрацию если нужно
            kwargs["queryset"] = db_field.related_model.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    # Оптимизация запросов
    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'model_line_item' ,
            'model_line_item__model_line' ,
            'power_supply'
        )
    def display_name(self, obj) :
        if obj.model_line_item and obj.power_supply:
            return f'{obj.model_line_item.name}.{obj.power_supply.encoding}'
        return "Не указано имя модели или напряжение"

    def display_params(self, obj) :
        if obj.model_line_item and obj.power_supply:
            return f'Iном={obj.motor_current_rated} / Istart={obj.motor_current_starting} / P={obj.motor_power}'
        return "Не указано имя модели или напряжение"
    # Проверка уникальности дефолтных опций
    def save_model(self , request , obj , form , change) :
        super().save_model(request , obj , form , change)
