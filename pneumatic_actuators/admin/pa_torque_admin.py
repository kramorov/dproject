from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.db.models import Q
from pneumatic_actuators.models.pa_torque import BodyThrustTorqueTable


class BodyThrustTorqueTableForm(forms.ModelForm) :
    """Форма для таблицы моментов/усилий"""

    class Meta :
        model = BodyThrustTorqueTable
        fields = '__all__'
        widgets = {
            'bto' : forms.NumberInput(attrs={'step' : '0.1' , 'style' : 'width: 120px;'}) ,
            'rto' : forms.NumberInput(attrs={'step' : '0.1' , 'style' : 'width: 120px;'}) ,
            'eto' : forms.NumberInput(attrs={'step' : '0.1' , 'style' : 'width: 120px;'}) ,
        }

    def clean(self) :
        cleaned_data = super().clean()
        body = cleaned_data.get('body')
        pressure = cleaned_data.get('pressure')
        spring_qty = cleaned_data.get('spring_qty')

        # Проверка уникальности комбинации body + pressure + spring_qty
        if body and pressure and spring_qty :
            existing = BodyThrustTorqueTable.objects.filter(
                body=body ,
                pressure=pressure ,
                spring_qty=spring_qty
            )
            if self.instance :
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists() :
                raise forms.ValidationError(
                    _('Запись с такой комбинацией корпуса, давления и количества пружин уже существует.')
                )

        # Проверка значений моментов
        bto = cleaned_data.get('bto')
        rto = cleaned_data.get('rto')
        eto = cleaned_data.get('eto')

        if bto is not None and bto < 0 :
            raise forms.ValidationError({'bto' : _('Момент не может быть отрицательным')})
        if rto is not None and rto < 0 :
            raise forms.ValidationError({'rto' : _('Момент не может быть отрицательным')})
        if eto is not None and eto < 0 :
            raise forms.ValidationError({'eto' : _('Момент не может быть отрицательным')})

        return cleaned_data


class BodyThrustTorqueTableInline(admin.TabularInline) :
    """
    Inline для редактирования моментов/усилий в админке корпусов
    """
    model = BodyThrustTorqueTable
    form = BodyThrustTorqueTableForm
    extra = 1
    verbose_name = _('Момент/усилие')
    verbose_name_plural = _('Моменты/усилия')

    fields = ('pressure' , 'spring_qty' , 'bto' , 'rto' , 'eto')
    ordering = ('pressure__sorting_order' , 'spring_qty__sorting_order')
    # actions = ['export_selected_data']
    # Автодополнение для полей
    # autocomplete_fields = ['pressure' , 'spring_qty']

    def get_queryset(self , request) :
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related('pressure' , 'spring_qty')


class PressureFilter(admin.SimpleListFilter) :
    """Фильтр по давлению"""
    title = _('Давление')
    parameter_name = 'pressure'

    def lookups(self , request , model_admin) :
        pressures = BodyThrustTorqueTable.objects.values_list(
            'pressure__id' , 'pressure__name'
        ).distinct().order_by('pressure__sorting_order')
        return [(id , name) for id , name in pressures if name]

    def queryset(self , request , queryset) :
        if self.value() :
            return queryset.filter(pressure__id=self.value())
        return queryset


class SpringQtyFilter(admin.SimpleListFilter) :
    """Фильтр по количеству пружин"""
    title = _('Пружины/DA')
    parameter_name = 'spring_qty'

    def lookups(self , request , model_admin) :
        spring_qtys = BodyThrustTorqueTable.objects.values_list(
            'spring_qty__id' , 'spring_qty__name'
        ).distinct().order_by('spring_qty__sorting_order')
        return [(id , name) for id , name in spring_qtys if name]

    def queryset(self , request , queryset) :
        if self.value() :
            return queryset.filter(spring_qty__id=self.value())
        return queryset


@admin.register(BodyThrustTorqueTable)
class BodyThrustTorqueTableAdmin(admin.ModelAdmin) :
    """Админка для таблицы моментов/усилий пневмоприводов"""

    form = BodyThrustTorqueTableForm
    list_display = (
        'body' , 'pressure' , 'spring_qty' ,
        'bto', 'rto', 'eto',  # ← ИСПОЛЬЗУЙТЕ ПРЯМЫЕ ИМЕНА ПОЛЕЙ
        'is_da_actuator'
    )
    list_editable = ('bto' , 'rto' , 'eto')
    list_filter = (
        'body' ,
        PressureFilter ,
        SpringQtyFilter ,
    )
    search_fields = (
        'body__name' ,
        'body__code' ,
        'pressure__name' ,
        'spring_qty__name' ,
    )
    ordering = ('body__sorting_order' , 'pressure__sorting_order' , 'spring_qty__sorting_order')

    # Поля для автодополнения в форме
    # autocomplete_fields = ['body' , 'pressure' , 'spring_qty']

    fieldsets = (
        (_('Основные параметры') , {
            'fields' : (
                'body' , 'pressure' , 'spring_qty'
            )
        }) ,
        (_('Моменты/усилия') , {
            'fields' : (
                'bto' , 'rto' , 'eto'
            ) ,
            'description' : _(
                'BTO - момент страгивания для открытия, '
                'RTO - момент в среднем положении, '
                'ETO - конечный момент открытия'
            )
        }) ,
    )

    def get_queryset(self , request) :
        """Оптимизация запросов к базе данных"""
        return super().get_queryset(request).select_related(
            'body' , 'pressure' , 'spring_qty'
        )

    def bto_display(self , obj) :
        """Отображение BTO с единицами измерения"""
        return f"{obj.bto} Н·м" if obj.bto else "-"

    bto_display.short_description = _('BTO')
    bto_display.admin_order_field = 'bto'

    def rto_display(self , obj) :
        """Отображение RTO с единицами измерения"""
        return f"{obj.rto} Н·м" if obj.rto else "-"

    rto_display.short_description = _('RTO')
    rto_display.admin_order_field = 'rto'

    def eto_display(self , obj) :
        """Отображение ETO с единицами измерения"""
        return f"{obj.eto} Н·м" if obj.eto else "-"

    eto_display.short_description = _('ETO')
    eto_display.admin_order_field = 'eto'

    def is_da_actuator(self , obj) :
        """Показывает, является ли привод двойного действия"""
        return obj.spring_qty and obj.spring_qty.code == 'DA'

    is_da_actuator.short_description = _('DA')
    is_da_actuator.boolean = True

    def get_readonly_fields(self , request , obj=None) :
        """Поля только для чтения"""
        # Можно сделать некоторые поля readonly при необходимости
        return []

    def save_model(self , request , obj , form , change) :
        """Дополнительная логика при сохранении"""
        # Для приводов DA устанавливаем одинаковые значения моментов
        if obj.spring_qty and obj.spring_qty.code == 'DA' :
            if obj.bto and not obj.rto :
                obj.rto = obj.bto
            if obj.bto and not obj.eto :
                obj.eto = obj.bto

        super().save_model(request , obj , form , change)

    def formfield_for_foreignkey(self , db_field , request , **kwargs) :
        """Ограничение выбора для связанных полей"""
        if db_field.name == "spring_qty" :
            # Можно ограничить queryset для spring_qty если нужно
            kwargs["queryset"] = db_field.related_model.objects.filter(is_active=True)
        elif db_field.name == "pressure" :
            kwargs["queryset"] = db_field.related_model.objects.filter(is_active=True)
        elif db_field.name == "body" :
            kwargs["queryset"] = db_field.related_model.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field , request , **kwargs)

    class Media :
        css = {
            'all' : ('admin/css/pneumatic_torque.css' ,)
        }



# Добавляем inline в админку корпусов
from pneumatic_actuators.admin.pa_body_admin import PneumaticActuatorBodyAdmin
from pneumatic_actuators.models.pa_body import PneumaticActuatorBody

# Добавляем inline к существующей админке корпусов
PneumaticActuatorBodyAdmin.inlines += [BodyThrustTorqueTableInline]