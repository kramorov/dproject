# pneumatic_actuators/admin/pa_model_line_item_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html

from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
from pneumatic_actuators.models.pa_options import (
    PneumaticSafetyPositionOption,
    PneumaticSpringsQtyOption
)


class PneumaticSafetyPositionOptionInline(admin.TabularInline):
    """Inline для опций положения безопасности"""
    model = PneumaticSafetyPositionOption
    extra = 0
    ordering = ['is_default', 'sorting_order']
    fields = ['safety_position', 'encoding', 'is_default', 'is_active', 'sorting_order']
    verbose_name = _("Опция положения безопасности")
    verbose_name_plural = _("Опции положения безопасности")
    fk_name = 'model_line_item'  # Явно указываем поле связи

class PneumaticSpringsQtyOptionInline(admin.TabularInline):
    """Inline для опций количества пружин"""
    model = PneumaticSpringsQtyOption
    extra = 0
    ordering = ['is_default', 'sorting_order']
    fields = ['springs_qty', 'encoding', 'is_default', 'is_active', 'sorting_order']
    verbose_name = _("Опция количества пружин")
    verbose_name_plural = _("Опции количества пружин")
    fk_name = 'model_line_item'  # Явно указываем поле связи


@admin.register(PneumaticActuatorModelLineItem)
class PneumaticActuatorModelLineItemAdmin(admin.ModelAdmin):
    """Админка для моделей в серии пневмоприводов"""

    list_display = (
        'name',
        'code',
        'model_line',
        'body',
        'brand_display',
        'pneumatic_actuator_variety',
        'sorting_order',
        'is_active',
        'copy_item_action'
    )

    list_editable = ('sorting_order', 'is_active')
    list_filter = (
        'is_active',
        'model_line',
        'pneumatic_actuator_variety',
        'model_line__brand',
        'body',
    )

    search_fields = (
        'name',
        'code',
        'model_line__name',
        'body__name'
    )

    ordering = ('sorting_order', 'name')

    # Inline только для опций, которые принадлежат этой модели
    inlines = [
        PneumaticSafetyPositionOptionInline,
        PneumaticSpringsQtyOptionInline,
    ]

    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'name', 'code', 'description', 'sorting_order', 'is_active'
            )
        }),
        (_('Принадлежность'), {
            'fields': (
                'model_line',
                'pneumatic_actuator_variety',
                'body'
            )
        }),
    )

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related(
            'model_line',
            'model_line__brand',
            'model_line__pneumatic_actuator_construction_variety',
            'pneumatic_actuator_variety',
            'body'
        ).prefetch_related(
            'safety_position_option_model_line_item',
            'springs_qty_option_model_line_item'
        )

    def brand_display(self, obj):
        """Отображение бренда из model_line"""
        return obj.brand.name if obj.brand else "-"

    brand_display.short_description = _('Бренд')
    brand_display.admin_order_field = 'model_line__brand__name'

    def construction_variety_display(self, obj):
        """Отображение типа конструкции из model_line"""
        return obj.pneumatic_actuator_construction_variety.name if obj.pneumatic_actuator_construction_variety else "-"

    construction_variety_display.short_description = _('Тип конструкции')
    construction_variety_display.admin_order_field = 'model_line__pneumatic_actuator_construction_variety__name'

    def copy_instance(self, request, object_id):
        """Копирование одной модели через отдельную кнопку"""
        try:
            original = self.get_object(request, object_id)
            if original is None:
                messages.error(request, 'Объект не найден')
                return redirect(reverse('admin:pneumatic_actuators_pneumaticactuatormodellineitem_changelist'))

            copy_obj = original.create_copy()
            messages.success(request, f'Модель "{original.name}" успешно скопирована как "{copy_obj.name}"')
            return redirect(
                reverse('admin:pneumatic_actuators_pneumaticactuatormodellineitem_change', args=[copy_obj.pk]))

        except Exception as e:
            messages.error(request, f'Ошибка при копировании: {str(e)}')
            return redirect(reverse('admin:pneumatic_actuators_pneumaticactuatormodellineitem_changelist'))

    def copy_selected(self, request, queryset):
        """Копирование выбранных моделей через action"""
        count = 0
        for original in queryset:
            try:
                copy_obj = original.create_copy()
                count += 1
            except Exception as e:
                messages.error(request, f'Ошибка при копировании "{original.name}": {str(e)}')

        if count > 0:
            messages.success(request, f'Успешно скопировано {count} моделей')
        else:
            messages.warning(request, 'Не удалось скопировать ни одной модели')

    copy_selected.short_description = _('Сделать копии выбранных элементов')
    actions = ['copy_selected']

    def copy_item_action(self, obj):
        """Кнопка для копирования элемента в списке"""
        return format_html(
            '<a class="button" href="{}">Копировать</a>',
            reverse('admin:copy_model_line_item', args=[obj.pk])
        )

    copy_item_action.short_description = _('Действие')

    def get_urls(self):
        """Добавление кастомных URL"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/copy/',
                self.admin_site.admin_view(self.copy_instance),
                name='copy_model_line_item',
            ),
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        """Сохранение модели"""
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """Обработка сохранения inline форм"""
        instances = formset.save(commit=False)

        for instance in instances:
            # Убеждаемся, что связь с родительской моделью установлена
            if hasattr(instance, 'model_line_item') and not instance.model_line_item:
                instance.model_line_item = form.instance
            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()

    # Свойства для отображения в админке (наследуемые из model_line)
    def temperature_range_display(self, obj):
        """Отображение температурного диапазона"""
        return obj.temperature_range_display

    temperature_range_display.short_description = _('Температура')

    def ip_display(self, obj):
        """Отображение IP защиты"""
        return obj.ip_display

    ip_display.short_description = _('IP защита')

    def exd_display(self, obj):
        """Отображение взрывозащиты"""
        return obj.exd_display

    exd_display.short_description = _('Взрывозащита')

    def body_coating_display(self, obj):
        """Отображение покрытия корпуса"""
        return obj.body_coating_display

    body_coating_display.short_description = _('Покрытие')

    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }