# pneumatic_actuators/filters.py

import django_filters
from django import forms
from django.db import models
from .models import (
    PneumaticActuatorSelected ,
    PneumaticActuatorModelLineItem ,
)
from .models.pa_options import PneumaticSafetyPositionOption , PneumaticSpringsQtyOption , PneumaticTemperatureOption , \
    PneumaticIpOption , PneumaticExdOption , PneumaticBodyCoatingOption , PneumaticHandWheelOption


def get_used_queryset(model , field_name , filter_field='id' , exclude_null=True) :
    """
    Возвращает queryset объектов, которые реально используются в PneumaticActuatorSelected
    """
    filter_kwargs = {}
    if exclude_null :
        filter_kwargs[f"{field_name}__isnull"] = False

    used_ids = PneumaticActuatorSelected.objects.filter(
        **filter_kwargs
    ).values_list(field_name , flat=True).distinct()

    return model.objects.filter(**{f"{filter_field}__in" : used_ids})


class PneumaticActuatorSelectedFilter(django_filters.FilterSet) :
    """Фильтр для расширенного поиска выбранных приводов"""

    # Текстовые поля
    code = django_filters.CharFilter(
        field_name='code' ,
        lookup_expr='icontains' ,
        widget=forms.TextInput(attrs={'class' : 'form-control' , 'placeholder' : 'Введите код' , 'size' : 30})
    )

    name = django_filters.CharFilter(
        field_name='name' ,
        lookup_expr='icontains' ,
        widget=forms.TextInput(attrs={'class' : 'form-control' , 'placeholder' : 'Введите название' , 'size' : 30})
    )

    # Внешние ключи
    selected_model_line_item = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticActuatorModelLineItem , 'selected_model_line_item') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    selected_safety_position = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticSafetyPositionOption , 'selected_safety_position') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    selected_springs_qty = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticSpringsQtyOption , 'selected_springs_qty') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    selected_temperature = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticTemperatureOption , 'selected_temperature') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    selected_ip = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticIpOption , 'selected_ip') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    selected_exd = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticExdOption , 'selected_exd') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    selected_body_coating = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticBodyCoatingOption , 'selected_body_coating') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    selected_hand_wheel = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticHandWheelOption , 'selected_hand_wheel') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    # Булевы поля
    is_active = django_filters.BooleanFilter(
        widget=forms.Select(
            choices=[('' , 'Все') , ('true' , 'Активные') , ('false' , 'Неактивные')] ,
            attrs={'class' : 'form-control'}
        )
    )

    is_unique = django_filters.BooleanFilter(
        widget=forms.Select(
            choices=[('' , 'Все') , ('true' , 'Уникальные') , ('false' , 'Дубликаты')] ,
            attrs={'class' : 'form-control'}
        )
    )

    class Meta :
        model = PneumaticActuatorSelected
        fields = []

    @property
    def qs(self) :
        parent = super().qs
        return parent.select_related(
            'selected_model_line_item' ,
            'selected_safety_position' ,
            'selected_springs_qty' ,
            'selected_temperature' ,
            'selected_ip' ,
            'selected_exd' ,
            'selected_body_coating' ,
            'selected_hand_wheel'
        )