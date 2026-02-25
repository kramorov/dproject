# electric_actuators/admin/ea_model_line_item_options_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db import transaction
from django.utils.html import format_html
from typing import List, Optional, Tuple, Any, Dict, Union
from electric_actuators.models.ea_model_line_item_options import ElectricPowerSupplyOption, ElectricControlUnitOption
import logging
logger = logging.getLogger(__name__)

# def copy_power_option_action(modeladmin , request , queryset) :
#     """Копировать выбранные модели электроприводов"""
#     success_count = 0
#     error_count = 0
#
#     for original_item in queryset :
#         try :
#             with transaction.atomic() :
#                 # Используем метод create_copy модели
#                 copy_item = original_item.create_copy()
#                 success_count += 1
#                 logger.info(f"Скопирована опция: {original_item.display_name} -> {copy_item.display_name}")
#
#         except Exception as e :
#             error_count += 1
#             logger.error(f"Ошибка копирования {original_item}: {e}" , exc_info=True)
#             messages.error(
#                 request ,
#                 f"Ошибка при копировании '{original_item.display_name}': {str(e)[:100]}"
#             )
#
#     if success_count > 0 :
#         messages.success(request , f"Успешно скопировано {success_count} моделей.")
#     if error_count > 0 :
#         messages.warning(request , f"Не удалось скопировать {error_count} моделей.")
#
#
# copy_power_option_action.short_description = _("Копировать выбранные опции")

class ElectricControlUnitOptionInline(admin.TabularInline):
    """Inline для опций блоков управления"""
    model = ElectricControlUnitOption
    extra = 0
    ordering = ['sorting_order']

    fields = [
        'control_unit',
        'encoding',
        'is_default',
        'is_active',
        'sorting_order'
    ]

    verbose_name = _("Опция блока управления")
    verbose_name_plural = _("Опции блоков управления")

    # Автодополнение для поиска блоков управления
    # autocomplete_fields = ['control_unit']

    # Можно добавить кастомные виджеты для полей
    # def formfield_for_dbfield(self, db_field, request, **kwargs):
    #     if db_field.name == 'encoding':
    #         kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={'size': '10'})
    #     elif db_field.name == 'power_consumption':
    #         kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={'size': '8'})
    #     return super().formfield_for_dbfield(db_field, request, **kwargs)


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
    list_display = ('display_name', 'id', 'encoding', 'display_params','sorting_order','is_active')
    list_filter = ('model_line_item__model_line','model_line_item', 'power_supply', 'is_active')
    list_editable = ['sorting_order', 'is_active']
    search_fields = ('model_line_item__name', 'power_supply__name', 'encoding')
    ordering = ('sorting_order', 'model_line_item', )

    fieldsets = (
        (None, {
            'fields': (
                ('model_line_item','power_supply','encoding'),
                ('is_active',
                'sorting_order'),
            )
        }),
        (_('Характеристики'), {
            'fields': (
                ('motor_current_rated',
                'motor_current_starting',
                'motor_power'),
            )
        }),
        (_('Нестандартные характеристики для этой модели с этим напряжением'), {
            'fields': (

                ('time_to_open',
                 'time_to_close'),
                ('torque_min',
                 'torque_max')
            )
        }),
        (_('Описание'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )
    inlines = [ElectricControlUnitOptionInline]
    # Добавляем кастомные методы для отображения в списке
    actions = [
        copy_electric_power_supply_option

    ]


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

    display_name.short_description = 'Модель'

    def display_params(self, obj) :
        if obj.model_line_item and obj.power_supply:
            return f'Iном={obj.motor_current_rated} / Istart={obj.motor_current_starting} / P={obj.motor_power}'
        return "Не указано имя модели или напряжение"

    display_params.short_description = 'Токи и мощность'

    # Проверка уникальности дефолтных опций
    def save_model(self , request , obj , form , change) :
        super().save_model(request , obj , form , change)

        # Добавляем метод для предотвращения дублирования дефолтных опций:
        def save_formset(self, request, form, formset, change):
            """Сохранение formset с валидацией"""
            if formset.model == ElectricControlUnitOption:
                instances = formset.save(commit=False)

                # Проверяем, что только одна опция помечена как дефолтная
                default_instances = [i for i in instances if i.is_default]

                if len(default_instances) > 1:
                    form.instance._default_validation_error = True
                    messages.error(
                        request,
                        'Только одна опция блока управления может быть помечена как "По умолчанию"'
                    )
                    return

                # Сохраняем все инстансы
                for instance in instances:
                    instance.save()
                formset.save_m2m()
            else:
                super().save_formset(request, form, formset, change)

        # Добавляем валидацию при сохранении:
        def save_model(self, request, obj, form, change):
            # Проверяем, была ли ошибка валидации в formset
            if hasattr(obj, '_default_validation_error'):
                delattr(obj, '_default_validation_error')
                return  # Не сохраняем, если была ошибка

            super().save_model(request, obj, form, change)