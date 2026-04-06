# solenoid_valves/admin.py
from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
import logging
logger = logging.getLogger(__name__)

from core.models.mixins import AdminStructuredDataMixinCopyMixin
from .models import (
    ValveDesign ,
    ValveOperationVariety ,
    ValveFunction ,
    ValveActuationVariety , ManualOverride , ValvePilotVariety , DirectionValve , DirectionalValveModelLine ,
    DirectionValveBody
)
from electric_actuators.models import CableGlandHolesSet

@admin.register(ValveDesign)
class ValveDesignAdmin(AdminStructuredDataMixinCopyMixin,admin.ModelAdmin):
    list_display = ('name', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('name', 'code')
    actions = ['copy_objects']  # Явно добавляем action

@admin.register(ValveOperationVariety)
class ValveOperationVarietyAdmin(AdminStructuredDataMixinCopyMixin,admin.ModelAdmin):
    list_display = ('name', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('name', 'code')
    actions = ['copy_objects']  # Явно добавляем action

@admin.register(ValveFunction)
class ValveFunctionAdmin(AdminStructuredDataMixinCopyMixin,admin.ModelAdmin):
    list_display = ('name', 'ports_count', 'positions_count', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('ports_count', 'positions_count', 'is_active')
    search_fields = ('name', 'code')
    # Группировка полей в форме редактирования
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description')
        }),
        ('Технические параметры', {
            'fields': ('ports_count', 'positions_count'),
            'description': 'Параметры линейности и позиционности'
        }),
        ('Настройки отображения', {
            'fields': ('sorting_order', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    actions = ['copy_objects']  # Явно добавляем action

@admin.register(ValveActuationVariety)
class ValveActuationVarietyAdmin(AdminStructuredDataMixinCopyMixin,admin.ModelAdmin):
    list_display = ('name', 'return_category', 'solenoids_count', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('return_category', 'solenoids_count', 'is_active')
    search_fields = ('name', 'code')
    # prepopulated_fields = {'code': ('name',)} # Автогенерация кода из названия
    actions = ['copy_objects']  # Явно добавляем action

@admin.register(ManualOverride)
class ManualOverrideAdmin(admin.ModelAdmin) :
    list_display = ('name' , 'mechanism' , 'has_fixation' , 'code' , 'sorting_order' , 'is_active')
    list_editable = ('sorting_order' , 'is_active' , 'has_fixation')
    list_filter = ('mechanism' , 'has_fixation' , 'is_active')
    search_fields = ('name' , 'code')
    # prepopulated_fields = {'code' : ('name' ,)}

@admin.register(ValvePilotVariety)
class ValvePilotTypeAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    list_display = ('name', 'category', 'code', 'sorting_order', 'is_active')
    list_filter = ('category', 'is_active')
    # prepopulated_fields = {'code': ('name',)}
    actions = ['copy_selected_objects']


# ==================== FORMS ====================

class DirectionalValveModelLineForm(forms.ModelForm) :
    """Форма для серии распределительных клапанов"""

    class Meta :
        model = DirectionalValveModelLine
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(attrs={
                'size' : 80 ,
                'style' : 'width: 80%' ,
                'placeholder' : 'Введите название серии'
            }) ,
            'code' : forms.TextInput(attrs={
                'size' : 30 ,
                'style' : 'width: 50%'
            }) ,
            'name_template' : forms.Textarea(attrs={
                'rows' : 4 ,
                'cols' : 80 ,
                'style' : 'width: 90%' ,
                'placeholder' : 'Шаблон для генерации названия (например: "Клапан {function} {size}")'
            }) ,
            'description_template' : forms.Textarea(attrs={
                'rows' : 4 ,
                'cols' : 80 ,
                'style' : 'width: 90%' ,
                'placeholder' : 'Шаблон для генерации описания'
            }) ,
            'description' : forms.Textarea(attrs={
                'rows' : 4 ,
                'cols' : 80 ,
                'style' : 'width: 90%'
            }) ,
        }


class DirectionValveBodyForm(forms.ModelForm) :
    """Форма для корпуса клапана"""

    class Meta :
        model = DirectionValveBody
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(attrs={
                'size' : 80 ,
                'style' : 'width: 80%' ,
                'placeholder' : 'Введите название корпуса'
            }) ,
            'code' : forms.TextInput(attrs={
                'size' : 30 ,
                'style' : 'width: 50%'
            }) ,
            'description' : forms.Textarea(attrs={
                'rows' : 4 ,
                'cols' : 80 ,
                'style' : 'width: 90%'
            }) ,
            'weight' : forms.NumberInput(attrs={
                'style' : 'width: 150px' ,
                'placeholder' : 'кг' ,
                'step' : '0.01'
            }) ,
        }


class DirectionValveForm(forms.ModelForm) :
    """Форма для распределительного клапана"""

    class Meta :
        model = DirectionValve
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(attrs={
                'size' : 80 ,
                'style' : 'width: 80%' ,
                'placeholder' : 'Введите название клапана'
            }) ,
            # 'code' : forms.TextInput(attrs={
            #     'size' : 20 ,
            #     'style' : 'width: 50%'
            # }) ,
            # 'description' : forms.Textarea(attrs={
            #     'rows' : 4 ,
            #     'cols' : 80 ,
            #     'style' : 'width: 90%'
            # }) ,
            'kv' : forms.NumberInput(attrs={
                'style' : 'width: 120px' ,
                'placeholder' : 'м³/ч' ,
                'step' : '0.01'
            }) ,
            'dn' : forms.NumberInput(attrs={
                'style' : 'width: 120px' ,
                'placeholder' : 'мм' ,
                'step' : '0.01'
            }) ,
            'power_consumption_start' : forms.NumberInput(attrs={
                'style' : 'width: 120px' ,
                'placeholder' : 'Вт' ,
                'step' : '0.01'
            }) ,
            'power_consumption_hot' : forms.NumberInput(attrs={
                'style' : 'width: 120px' ,
                'placeholder' : 'Вт' ,
                'step' : '0.01'
            }) ,
            'pressure_min' : forms.NumberInput(attrs={
                'style' : 'width: 120px' ,
                'placeholder' : 'бар' ,
                'step' : '0.01'
            }) ,
            'pressure_max' : forms.NumberInput(attrs={
                'style' : 'width: 120px' ,
                'placeholder' : 'бар' ,
                'step' : '0.01'
            }) ,
            'work_temp_min' : forms.NumberInput(attrs={
                'style' : 'width: 100px' ,
                'placeholder' : '°C'
            }) ,
            'work_temp_max' : forms.NumberInput(attrs={
                'style' : 'width: 100px' ,
                'placeholder' : '°C'
            }) ,
            'medium_density_max' : forms.NumberInput(attrs={
                'style' : 'width: 120px' ,
                'placeholder' : 'сСт' ,
                'step' : '0.01'
            }) ,
            'weight' : forms.NumberInput(attrs={
                'style' : 'width: 120px' ,
                'placeholder' : 'кг' ,
                'step' : '0.01'
            }) ,
        }


# ==================== ADMIN CLASSES ====================

@admin.register(DirectionalValveModelLine)
class DirectionalValveModelLineAdmin(AdminStructuredDataMixinCopyMixin , admin.ModelAdmin) :
    """
    Админка для серии распределительных клапанов (DNA клапана)
    """
    form = DirectionalValveModelLineForm

    list_display = [
        'name' , 'code' , 'brand' , 'construction' , 'operation' ,
        'working_medium' ,  'exd' , 'sorting_order' , 'is_active'
    ]
    list_editable = ['sorting_order' , 'is_active']
    list_filter = [
        'is_active' , 'brand' , 'construction' , 'operation' ,
        'working_medium' , 'exd' , 'solenoid_insulation_class'
    ]
    search_fields = ['name' , 'code' , 'description']

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , 'code' , 'description')
        }) ,
        (_('Шаблоны генерации') , {
            'fields' : ('name_template' , 'description_template') ,
            'description' : _('Шаблоны для автоматической генерации названий и описаний конкретных клапанов')
        }) ,
        (_('Производитель и бренд') , {
            'fields' : ('producer' , 'brand') ,
            'classes' : ('collapse' ,)
        }) ,
        (_('Конструктивные характеристики (DNA)') , {
            'fields' : (
                'construction' ,
                'operation' ,
                'working_medium' ,
            ) ,
            'description' : _('Эти параметры определяют уникальность серии')
        }) ,
        (_('Защита и изоляция') , {
            'fields' : (
                'exd' ,
                'solenoid_insulation_class' ,
            ) ,
        }) ,
        (_('Настройки отображения') , {
            'fields' : ('sorting_order' , 'is_active') ,
            'classes' : ('collapse' ,)
        }) ,
    )

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'producer' , 'brand' , 'construction' , 'operation' ,
            'working_medium' , 'exd'
        )


@admin.register(DirectionValveBody)
class DirectionValveBodyAdmin(AdminStructuredDataMixinCopyMixin , admin.ModelAdmin) :
    """
    Админка для корпуса клапана
    """
    form = DirectionValveBodyForm

    list_display = [
        'name' , 'code' , 'brand' ,  'get_valves_count' ,
        'sorting_order' , 'is_active'
    ]
    list_editable = ['sorting_order' , 'is_active']
    list_filter = [
        'is_active' , 'brand' ,
    ]
    search_fields = ['name' , 'code' , 'brand__name' , 'description']

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , 'code' , 'description')
        }) ,
        (_('Производитель и бренд') , {
            'fields' : ('brand' ,) ,
        }) ,
        (_('Настройки отображения') , {
            'fields' : ('sorting_order' , 'is_active') ,
            'classes' : ('collapse' ,)
        }) ,
    )

    def get_valves_count(self , obj) :
        """Количество клапанов, использующих этот корпус"""
        count = obj.direction_valve_body.count()
        return count if count > 0 else '-'

    get_valves_count.short_description = _('Используется в клапанах')
    get_valves_count.admin_order_field = 'direction_valve_body__count'


@admin.register(DirectionValve)
class DirectionValveAdmin(AdminStructuredDataMixinCopyMixin , admin.ModelAdmin) :
    """
    Админка для распределительного клапана (конкретный артикул)
    """
    form = DirectionValveForm

    list_display = [
        'code' , 'model_line' , 'function' ,
        'power_supply' , 'work_temp_min', 'work_temp_max','ip' ,
        'body_material' , 'solenoid_body_material', 'sorting_order' ,
    ]
    list_editable = ['sorting_order','ip' ]
    list_filter = [
        'is_active' , 'model_line' , 'function' , 'actuation' ,
        'power_supply' , 'brand' , 'ip' ,
        'body_material' , 'solenoid_body_material' , 'work_temp_min'
    ]
    search_fields = ['name' , 'code' , 'description' , 'model_line__name']
    # autocomplete_fields = [
    #     'model_line' , 'body' , 'function' , 'actuation' ,
    #     'manual_override' , 'power_supply' , 'producer' ,
    #     'brand' , 'body_material' , 'sealing_material' ,
    #     'solenoid_body_material' , 'body_material_specified' ,
    #     'ip' , 'pneumatic_connection' , 'pneumatic_connection_thread'
    # ]

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ( 'code' , 'model_line')
        }) ,
        (_('Производитель и бренд') , {
            'fields' : (('name' , 'description' ,), ('producer' , 'brand') ),
            'classes' : ('collapse' ,)
        }) ,
        (_('Функциональные характеристики') , {
            'fields' : (
                ('function' , 'actuation', 'manual_override' ,) ,
                ('dn' , 'kv', 'ip' ,) ,
            ) ,
        }) ,
        (_('Корпус') , {
            'fields' : (
                'body' ,
                'weight' ,
                ('pneumatic_connection' , 'pneumatic_connection_thread','cable_glands_holes') ,
                ('body_material', 'body_material_specified'),
                ('sealing_material_specified',),
                ('solenoid_body_material', 'solenoid_body_material_specified'),
            ) ,
        }) ,
        (_('Рабочие параметры') , {
            'fields' : (
                ('pressure_min' , 'pressure_max') ,
                ('work_temp_min' , 'work_temp_max') ,
                'medium_density_max' ,
            ) ,
        }) ,
        (_('Электрические характеристики') , {
            'fields' : (
                'power_supply' ,
                ('power_consumption_start' , 'power_consumption_hot', 'power_consumption_hold') ,
            ) ,
        }) ,
        (_('Настройки отображения') , {
            'fields' : ('sorting_order' , 'is_active') ,
            'classes' : ('collapse' ,)
        }) ,
    )

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'model_line' , 'body' , 'function' , 'actuation' ,
            'manual_override' , 'power_supply' , 'producer' , 'brand' ,
            'body_material' , 'sealing_material_specified' , 'solenoid_body_material' ,'solenoid_body_material_specified' ,
            'body_material_specified' , 'ip' , 'pneumatic_connection' ,
            'pneumatic_connection_thread'
        )

    def save_model(self , request , obj , form , change) :
        """При сохранении автоматически генерируем name из шаблона, если не задано"""
        if not obj.name and obj.model_line and obj.model_line.name_template :
            try :
                # Формируем словарь с данными для шаблона
                context = {
                    'function' : obj.function.name if obj.function else '' ,
                    'actuation' : obj.actuation.name if obj.actuation else '' ,
                    'dn' : obj.dn or '' ,
                    'pressure' : obj.pressure_max or '' ,
                    'code' : obj.code or '' ,
                }
                obj.name = obj.model_line.name_template.format(**context)
            except KeyError as e :
                logger.warning(f"Ошибка форматирования шаблона: {e}")
                obj.name = f"{obj.model_line.name} {obj.function} {obj.dn}мм"

        if not obj.description and obj.model_line and obj.model_line.description_template :
            try :
                context = {
                    'function' : obj.function.name if obj.function else '' ,
                    'actuation' : obj.actuation.name if obj.actuation else '' ,
                    'dn' : obj.dn or '' ,
                    'pressure' : obj.pressure_max or '' ,
                    'code' : obj.code or '' ,
                }
                obj.description = obj.model_line.description_template.format(**context)
            except KeyError as e :
                logger.warning(f"Ошибка форматирования шаблона описания: {e}")

        super().save_model(request , obj , form , change)

    def copy_selected_valves(self, request, queryset):
        """Action для копирования выбранных моделей клапанов"""
        copied_count = 0

        for valve in queryset:
            # Используем встроенный метод create_copy()
            # Он автоматически:
            # 1. Обработает преобразования полей (name, code, sorting_order)
            # 2. Сохранит копию в БД
            copy_obj = valve.create_copy(save_copy=True)
            copied_count += 1

        self.message_user(
            request,
            f'Успешно скопировано {copied_count} клапанов',
        )

    actions = ['copy_selected_valves']
    copy_selected_valves.short_description = "Копировать выбранные модели клапанов"