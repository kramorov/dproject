# solenoid_valves/filters.py

import django_filters
from django import forms
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import (
    DirectionValve , DirectionalValveModelLine , ValveFunction ,
    ValveActuationVariety , MaterialGeneral , MaterialSpecified ,
    PowerSupplies , ManualOverride , ThreadSize , PneumaticConnection ,
    Brands
)


def get_used_queryset(model , field_name , filter_field='id' , exclude_null=True) :
    """
    Возвращает queryset объектов, которые реально используются в DirectionValve

    Args:
        model: Модель, для которой строим queryset (MaterialGeneral, MaterialSpecified и т.д.)
        field_name: Имя поля в DirectionValve, по которому фильтруем
        filter_field: Поле в связанной модели для фильтрации (обычно 'id')
        exclude_null: Исключать NULL значения

    Returns:
        QuerySet: отфильтрованный queryset
    """
    # Базовый фильтр для DirectionValve
    filter_kwargs = {}
    if exclude_null :
        filter_kwargs[f"{field_name}__isnull"] = False

    # Получаем ID используемых объектов
    used_ids = DirectionValve.objects.filter(
        **filter_kwargs
    ).values_list(field_name , flat=True).distinct()

    # Возвращаем queryset только с используемыми объектами
    return model.objects.filter(**{f"{filter_field}__in" : used_ids})


class DirectionValveFilter(django_filters.FilterSet) :
    """Фильтр для расширенного поиска клапанов"""

    # ========== Текстовые поля (поиск по подстроке) ==========
    code = django_filters.CharFilter(
        field_name='code' ,
        lookup_expr='icontains' ,
        widget=forms.TextInput(attrs={
            'class' : 'form-control' ,
            'placeholder' : 'Введите код (подстрока)' ,
            'size' : 25
        })
    )

    # ========== Внешние ключи (только используемые значения) ==========
    model_line = django_filters.ModelChoiceFilter(
        queryset=DirectionalValveModelLine.objects.filter(
            id__in=DirectionValve.objects.filter(
                model_line__isnull=False
            ).values_list('model_line' , flat=True).distinct()
        ) ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    brand = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(Brands , 'brand') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    function = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(ValveFunction , 'function') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    ip = django_filters.ModelChoiceFilter(
        queryset=None ,  # Будет заполнено в __init__
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    exd = django_filters.ModelChoiceFilter(
        queryset=None ,  # Будет заполнено в __init__
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    actuation = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(ValveActuationVariety , 'actuation') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    manual_override = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(ManualOverride , 'manual_override') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    power_supply = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PowerSupplies , 'power_supply') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    body_material = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(MaterialGeneral , 'body_material') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    sealing_material_specified = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(MaterialSpecified , 'sealing_material_specified') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    solenoid_body_material = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(MaterialGeneral , 'solenoid_body_material') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    pneumatic_connection_thread = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(ThreadSize , 'pneumatic_connection_thread') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    pneumatic_connection = django_filters.ModelChoiceFilter(
        queryset=get_used_queryset(PneumaticConnection , 'pneumatic_connection') ,
        widget=forms.Select(attrs={'class' : 'form-control'})
    )

    # ========== Числовые поля ==========
    kv_min = django_filters.NumberFilter(
        field_name='kv' ,
        lookup_expr='gte' ,
        widget=forms.NumberInput(attrs={'class' : 'form-control' , 'placeholder' : 'от' , 'style' : 'width: 80px'})
    )
    kv_max = django_filters.NumberFilter(
        field_name='kv' ,
        lookup_expr='lte' ,
        widget=forms.NumberInput(attrs={'class' : 'form-control' , 'placeholder' : 'до' , 'style' : 'width: 80px'})
    )

    # Расход в минуту (л/мин) - вычисляемое поле через аннотацию
    flow_rate_min = django_filters.NumberFilter(
        method='filter_flow_rate_min' ,
        widget=forms.NumberInput(attrs={'class' : 'form-control' , 'placeholder' : 'от' , 'style' : 'width: 80px'})
    )
    flow_rate_max = django_filters.NumberFilter(
        method='filter_flow_rate_max' ,
        widget=forms.NumberInput(attrs={'class' : 'form-control' , 'placeholder' : 'до' , 'style' : 'width: 80px'})
    )

    work_temp_min = django_filters.NumberFilter(
        field_name='work_temp_min' ,
        lookup_expr='lte' ,  # меньше или равно
        label=_("Мин. рабочая температура (не выше)") ,
        widget=forms.NumberInput(attrs={
            'class' : 'form-control' ,
            'placeholder' : '≤ °C' ,
            'style' : 'width: 120px'
        })
    )

    # ========== Булевы поля ==========
    is_active = django_filters.BooleanFilter(
        widget=forms.Select(
            choices=[('' , 'Все') , ('true' , 'Активные') , ('false' , 'Неактивные')] ,
            attrs={'class' : 'form-control'}
        )
    )

    class Meta :
        model = DirectionValve
        fields = []  # Поля определяем явно выше

    def __init__(self , *args , **kwargs) :
        super().__init__(*args , **kwargs)
        # Динамически заполняем queryset для ip и exd (только используемые значения)
        from params.models import IpOption , ExdOption

        # IP - только используемые в клапанах
        used_ip_ids = DirectionValve.objects.filter(
            ip__isnull=False
        ).values_list('ip' , flat=True).distinct()
        self.filters['ip'].queryset = IpOption.objects.filter(id__in=used_ip_ids)

        # Exd - только используемые в клапанах
        used_exd_ids = DirectionValve.objects.filter(
            exd__isnull=False
        ).values_list('exd' , flat=True).distinct()
        self.filters['exd'].queryset = ExdOption.objects.filter(id__in=used_exd_ids)

    def filter_flow_rate_min(self , queryset , name , value) :
        """Фильтр по минимальному расходу (л/мин) - конвертируем из Kv"""
        if value :
            # Kv пересчет в расход: Q = Kv * 1000 (л/мин)
            kv_min = float(value) / 1000
            return queryset.filter(kv__gte=kv_min)
        return queryset

    def filter_flow_rate_max(self , queryset , name , value) :
        """Фильтр по максимальному расходу (л/мин) - конвертируем из Kv"""
        if value :
            kv_max = float(value) / 1000
            return queryset.filter(kv__lte=kv_max)
        return queryset

    def filter_queryset(self , queryset) :
        """Расширенная фильтрация с поддержкой иерархии функций"""
        queryset = super().filter_queryset(queryset)

        # Специальная обработка для функции: если выбрана 3/2, включаем и 5/2
        function_value = self.data.get('function')
        if function_value :
            try :
                selected_function = ValveFunction.objects.get(id=function_value)
                # Если выбрана 3/2 или 5/2, ищем также похожие
                if selected_function.name in ['3/2' , '5/2' , '5/3'] :
                    queryset = queryset.filter(
                        models.Q(function_id=function_value) |
                        models.Q(function__name__icontains=selected_function.name[:3])
                    )
            except ValveFunction.DoesNotExist :
                pass

        return queryset

    @property
    def qs(self) :
        """Оптимизируем запросы с select_related и добавляем аннотации"""
        parent = super().qs

        # Добавляем аннотацию для расхода (л/мин)
        from django.db.models import F , ExpressionWrapper , FloatField

        parent = parent.annotate(
            flow_rate=ExpressionWrapper(
                F('kv') * 1000 ,
                output_field=FloatField()
            )
        )

        # Оптимизируем связанные запросы
        return parent.select_related(
            'model_line' ,
            'brand' ,
            'function' ,
            'ip' ,
            'exd' ,
            'actuation' ,
            'manual_override' ,
            'power_supply' ,
            'body_material' ,
            'sealing_material_specified' ,
            'solenoid_body_material' ,
            'pneumatic_connection_thread' ,
            'pneumatic_connection' ,
            'producer' ,
            'body'
        ).prefetch_related(
            'model_line__construction' ,
            'model_line__operation' ,
            'model_line__working_medium'
        )