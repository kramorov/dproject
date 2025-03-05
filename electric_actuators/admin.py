from django.contrib import admin

from django import forms
from django.urls import path  # Импортируем path
from django.shortcuts import render, redirect
from django.forms import TextInput, Textarea
from .models import ModelLine, ModelBody, ElectricActuatorData, ActualActuator, CableGlandHolesSet, WiringDiagram
import logging

from params.models import MeasureUnits, MountingPlateTypes, StemShapes, StemSize, \
    IpOption, BodyCoatingOption, ExdOption, BlinkerOption, SwitchesParameters, \
    ActuatorGearboxOutputType, EnvTempParameters, DigitalProtocolsSupportOption, ControlUnitInstalledOption, \
    HandWheelInstalledOption, OperatingModeOption


def copy_electric_actuator_data(modeladmin, request, queryset):
    for obj in queryset:
        # Копируем объект
        obj.pk = None  # Убираем primary key, чтобы создать новый объект
        obj.name = obj.name + '(Копия)'
        obj.save()


copy_electric_actuator_data.short_description = "Копировать выбранные записи"


class ModelBodyAdmin(admin.ModelAdmin):
    ordering = ['name']
    # Показать важные поля в списке объектов модели
    list_display = ('name', 'model_line', 'text_description', 'max_stem_height', 'max_stem_diameter')

    # Добавить фильтры для фильтрации по определенным полям
    list_filter = ('model_line', 'mounting_plate', 'stem_shape', 'stem_size')

    # Возможность поиска по полям
    search_fields = ('name', 'text_description', 'model_line__name')
    filter_horizontal = ('mounting_plate',)  # Это добавит горизонтальные чекбоксы для поля "mounting_plate"

    # Поля для редактирования в админке
    fieldsets = (
        ('Основные параметры', {
            'fields': ('name', 'model_line', 'text_description', )
        }),
        ('Опции и характеристики', {
            'fields': (('default_cable_glands_holes', 'allowed_cable_glands_holes'), 'mounting_plate', 'stem_shape',
                       'stem_size', 'max_stem_height',
                       'max_stem_diameter')
        }),
    )

    # # Поля для редактирования при добавлении или изменении записи
    # add_fieldsets = (
    #     ('Основные параметры', {
    #         'fields': ('name', 'model_line', 'text_description')
    #     }),
    #     ('Опции и характеристики', {
    #         'fields': ('cable_glands_holes', 'stem_shape', 'stem_size', 'max_stem_height',
    #                    'max_stem_diameter')
    #     }),
    # )

    # Отображение связанного объекта (например, когда поля из связанных моделей показываются в форме)
    def get_related_fieldsets(self, request, obj=None):
        if obj:
            return super().get_related_fieldsets(request, obj)
        return self.add_fieldsets  # если объект еще не создан, показываем поля для добавления

    # Возможность выбора отображаемых полей для инлайн-редактирования
    inlines = []  # Если есть инлайны для отображения других связанных объектов
    actions = [copy_electric_actuator_data]  # Добавляем действие для копирования


class ActualActuatorAdmin(admin.ModelAdmin):
    # Показать только нужные поля в списке
    # change_form_template = 'admin/electric_actuators/actualactuator/change_form.html'
    list_display = ('name', 'actual_model', 'date_created', 'date_updated', 'actual_time_to_open',
                    'actual_rotations_to_open',
                    'actual_stem_shape', 'actual_stem_size', 'actual_cable_glands_holes')

    # Фильтрация по полям
    list_filter = ('actual_model', 'status', 'actual_ip', 'actual_exd', 'actual_temperature')

    # Поиск по полям
    search_fields = ('name', 'actual_model__name', 'status')

    # class Meta:
    #     model = ActualActuator
    #     fields = '__all__'
    # def show_full_description_popup(self, request, pk):
    #     # logger.debug('Это отладочное сообщение show_full_description_popup (CableGlandItemAdmin)')
    #     obj = self.get_object(request, pk)
    #     full_description = obj.get_full_description()
    #
    #     context = {
    #         'full_description': full_description,
    #         'object': obj,
    #         'subtitle': 'Some subtitle value',  # Здесь добавляем subtitle
    #     }
    #
    #     return render(request, 'admin/full_description_popup.html', context)
    #
    # def get_urls(self):
    #     urls = super().get_urls()
    #     custom_urls = [
    #         path('show_description/<int:pk>/', self.show_full_description_popup),
    #         path('update_name/<int:pk>/', self.update_name_view),
    #     ]
    #     # print("Свои URLs для ActualActuatorAdmin : ", custom_urls)  # Print custom URLs to verify
    #     return custom_urls + urls
    #
    # def update_name_view(self, request, pk):
    #     obj = self.get_object(request, pk)
    #     if obj.actual_model:
    #         obj.name = obj.actual_model.name
    #         obj.save()
    #         self.message_user(request, f'Имя объекта обновлено на "{obj.name}"')
    #
    #     # После обновления перенаправляем назад на форму редактирования
    #     return redirect(f'/admin/{obj._meta.app_label}/{obj._meta.model_name}/{obj.pk}/')
    #
    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     """
    #     Мы переопределяем метод change_view, чтобы добавить нашу кнопку
    #     на страницу редактирования объекта.
    #     """
    #     extra_context = extra_context or {}
    #     extra_context['show_update_name_button'] = True  # Флаг для отображения кнопки
    #     return super().change_view(request, object_id, form_url, extra_context=extra_context)

    # Действие при изменении поля actual_model
    # def save_model(self, request, obj, form, change):
    #     if obj.actual_model and not change:  # Если actual_model был изменен или новый объект
    #         obj.init(obj.actual_model)  # Вызов метода для инициализации данных из модели actual_model
    #     elif obj.actual_model and change:  # Если изменили actual_model для существующей записи
    #         old_obj = ActualActuator.objects.get(id=obj.id)
    #         if old_obj.actual_model != obj.actual_model:
    #             obj.init(obj.actual_model)  # Вызов метода для инициализации данных из новой модели
    #
    #     super().save_model(request, obj, form, change)

    # Форма с кастомными полями
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == 'actual_model':
    #         kwargs['queryset'] = ElectricActuatorData.objects.all()  # Ограничить список моделей
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Форма для отображения полей
    # fieldsets = (
    #     ('Основные параметры', {
    #         'fields': ('name', 'actual_model', 'status')
    #     }),
    #     ('Опции привода', {
    #         'fields': ('actual_time_to_open', 'actual_time_to_open_measure_unit', 'actual_rotations_to_open',
    #                    'actual_rotations_to_open_measure_unit', 'actual_mounting_plate', 'actual_stem_shape',
    #                    'actual_stem_size', 'actual_cable_glands_holes', 'actual_wiring_diagram', 'actual_ip',
    #                    'actual_body_coating', 'actual_exd', 'actual_blinker', 'actual_end_switches',
    #                    'actual_way_switches', 'actual_torque_switches', 'actual_output_type', 'actual_temperature',
    #                    'actual_digital_protocol_support', 'actual_control_unit_installed', 'actual_hand_wheel',
    #                    'actual_operating_mode')
    #     }),
    #     ('Описание', {
    #         'fields': ('text_description',)
    #     }),
    # )


class WiringDiagramAdminForm(forms.ModelForm):
    class Meta:
        model = WiringDiagram
        fields = '__all__'

    applies_to_electric_actuators = forms.ModelMultipleChoiceField(
        queryset=ElectricActuatorData.objects.none(),  # initially empty queryset
        widget=forms.CheckboxSelectMultiple,
        required=False  # поле теперь необязательное
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'applies_to_model_line' in self.data:
            try:
                model_line_id = int(self.data.get('applies_to_model_line'))
                self.fields['applies_to_models'].queryset = ElectricActuatorData.objects.filter(
                    model_line_id=model_line_id)
            except (ValueError, TypeError):
                pass


class WiringDiagramAdmin(admin.ModelAdmin):
    form = WiringDiagramAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # if obj:  # for editing
        #     form.base_fields[
        #         'applies_to_electric_actuators'].queryset = obj.applies_to_model_line.electric_actuators.all()
        return form


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


admin.site.register(ModelLine, ModelLineAdmin)
# admin.site.register(ElectricActuatorData, ElectricActuatorDataAdmin)
admin.site.register(CableGlandHolesSet)
admin.site.register(WiringDiagram, WiringDiagramAdmin)
admin.site.register(ActualActuator, ActualActuatorAdmin)
admin.site.register(ModelBody, ModelBodyAdmin)
