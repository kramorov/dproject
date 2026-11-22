# pneumatic_actuators/admin/pa_torque_admin.py
from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from pneumatic_actuators.models.pa_torque import BodyThrustTorqueTable


class BodyThrustTorqueTableForm(forms.ModelForm) :
    """Форма для таблицы моментов/усилий (длинный формат: строка = точка)."""

    class Meta :
        model = BodyThrustTorqueTable
        fields = '__all__'
        widgets = {
            'value' : forms.NumberInput(attrs={'step' : '0.1' , 'style' : 'width: 120px;'}) ,
        }

    def clean(self) :
        cleaned_data = super().clean()
        body = cleaned_data.get('body')
        pressure = cleaned_data.get('pressure')
        spring_qty = cleaned_data.get('spring_qty')
        point = cleaned_data.get('point')

        if body and pressure and spring_qty and point :
            existing = BodyThrustTorqueTable.objects.filter(
                body=body ,
                pressure=pressure ,
                spring_qty=spring_qty ,
                point=point ,
            )
            if self.instance :
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists() :
                raise forms.ValidationError(
                    _('Запись с такой комбинацией корпуса, давления, пружин и точки уже существует.')
                )

        value = cleaned_data.get('value')
        if value is not None and value < 0 :
            raise forms.ValidationError({'value' : _('Момент не может быть отрицательным')})

        return cleaned_data


class BodyThrustTorqueTableInline(admin.TabularInline) :
    """Inline для редактирования моментов/усилий в админке корпусов"""
    model = BodyThrustTorqueTable
    form = BodyThrustTorqueTableForm
    extra = 1
    verbose_name = _('Момент/усилие')
    verbose_name_plural = _('Моменты/усилия')

    fields = ('pressure' , 'spring_qty' , 'point' , 'value')
    ordering = ('pressure__sorting_order' , 'spring_qty__sorting_order' , 'point__sorting_order')

    def get_queryset(self , request) :
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related('pressure' , 'spring_qty' , 'point')


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
            return queryset.filter(pressure_id=self.value())
        return queryset


class SpringQtyFilter(admin.SimpleListFilter) :
    """Фильтр по количеству пружин"""
    title = _('Пружины')
    parameter_name = 'spring_qty'

    def lookups(self , request , model_admin) :
        qs = BodyThrustTorqueTable.objects.values_list(
            'spring_qty__id' , 'spring_qty__name'
        ).distinct().order_by('spring_qty__sorting_order')
        return [(id , name) for id , name in qs if name]

    def queryset(self , request , queryset) :
        if self.value() :
            return queryset.filter(spring_qty_id=self.value())
        return queryset


@admin.register(BodyThrustTorqueTable)
class BodyThrustTorqueTableAdmin(admin.ModelAdmin) :
    """Админка для таблицы моментов/усилий пневмоприводов (строка = точка)."""

    form = BodyThrustTorqueTableForm
    list_display = (
        'body' , 'pressure' , 'spring_qty' , 'point' , 'value' , 'is_da_actuator'
    )
    list_editable = ('value' ,)
    list_filter = (
        'body' ,
        'point' ,
        PressureFilter ,
        SpringQtyFilter ,
    )
    search_fields = (
        'body__name' ,
        'body__code' ,
        'pressure__name' ,
        'spring_qty__name' ,
        'point__code' ,
    )
    ordering = ('body__sorting_order' , 'pressure__sorting_order' , 'spring_qty__sorting_order' , 'point__sorting_order')

    fieldsets = (
        (_('Основные параметры') , {
            'fields' : (
                'body' , 'pressure' , 'spring_qty' , 'point'
            )
        }) ,
        (_('Значение') , {
            'fields' : (
                'value' ,
            ) ,
            'description' : _(
                'Значение момента/усилия в точке. Пружина хранится в ориентации '
                'закрытия: BTC (начало закрытия), RTC (середина), ETC (посадка).'
            )
        }) ,
    )

    def get_queryset(self , request) :
        """Оптимизация запросов к базе данных"""
        return super().get_queryset(request).select_related(
            'body' , 'pressure' , 'spring_qty' , 'point'
        )

    def is_da_actuator(self , obj) :
        """Показывает, является ли привод двойного действия"""
        return obj.spring_qty and obj.spring_qty.code == 'DA'

    is_da_actuator.short_description = _('DA')
    is_da_actuator.boolean = True

    def get_readonly_fields(self , request , obj=None) :
        """Поля только для чтения"""
        return []

    def formfield_for_foreignkey(self , db_field , request , **kwargs) :
        """Ограничение выбора для связанных полей"""
        if db_field.name in ("spring_qty" , "pressure" , "point") :
            kwargs["queryset"] = db_field.related_model.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field , request , **kwargs)
