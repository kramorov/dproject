# solenoid_valves/admin/dv_model_line_item_admin.py
from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminStructuredDataMixinCopyMixin
from solenoid_valves.models import DirectionValve


class DirectionValveForm(forms.ModelForm):
    """Форма для распределительного клапана"""

    class Meta:
        model = DirectionValve
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'size': 80,
                'style': 'width: 80%',
                'placeholder': 'Введите название клапана'
            }),
            'kv': forms.NumberInput(attrs={
                'style': 'width: 120px',
                'placeholder': 'м³/ч',
                'step': '0.01'
            }),
            'dn': forms.NumberInput(attrs={
                'style': 'width: 120px',
                'placeholder': 'мм',
                'step': '0.01'
            }),
            'power_consumption_start': forms.NumberInput(attrs={
                'style': 'width: 120px',
                'placeholder': 'Вт',
                'step': '0.01'
            }),
            'power_consumption_hot': forms.NumberInput(attrs={
                'style': 'width: 120px',
                'placeholder': 'Вт',
                'step': '0.01'
            }),
            'pressure_min': forms.NumberInput(attrs={
                'style': 'width: 120px',
                'placeholder': 'бар',
                'step': '0.01'
            }),
            'pressure_max': forms.NumberInput(attrs={
                'style': 'width: 120px',
                'placeholder': 'бар',
                'step': '0.01'
            }),
            'work_temp_min': forms.NumberInput(attrs={
                'style': 'width: 100px',
                'placeholder': '°C'
            }),
            'work_temp_max': forms.NumberInput(attrs={
                'style': 'width: 100px',
                'placeholder': '°C'
            }),
            'medium_density_max': forms.NumberInput(attrs={
                'style': 'width: 120px',
                'placeholder': 'сСт',
                'step': '0.01'
            }),
            'weight': forms.NumberInput(attrs={
                'style': 'width: 120px',
                'placeholder': 'кг',
                'step': '0.01'
            }),
        }


@admin.register(DirectionValve)
class DirectionValveAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    """Админка для распределительного клапана (конкретный артикул)"""
    form = DirectionValveForm

    list_display = ['id',
        'code', 'image_gallery', 'exd', 'pneumatic_connection', 'model_line', 'function',
        'power_supply', 'work_temp_min', 'ip',
        'body_material', 'solenoid_body_material', 'sorting_order',
    ]
    list_editable = ['sorting_order', 'image_gallery', 'code']
    list_select_related = [
        'model_line', 'function', 'actuation', 'power_supply', 'brand',
        'ip', 'exd', 'body_material', 'solenoid_body_material',
        'pneumatic_connection',
    ]
    list_filter = [
        'is_active', 'model_line', 'function', 'actuation',
        'power_supply', 'brand', 'ip', 'exd',
        'body_material', 'solenoid_body_material', 'work_temp_min'
    ]
    search_fields = ['name', 'code', 'description', 'model_line__name']
    filter_horizontal = ('tech_docs',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('code', 'model_line')
        }),
        (_('Производитель и бренд'), {
            'fields': (('name', 'description'), ('producer', 'brand')),
            'classes': ('collapse',)
        }),
        (_('Функциональные характеристики'), {
            'fields': (
                ('function', 'actuation', 'manual_override'),
                ('dn', 'kv', 'ip'),
            ),
        }),
        (_('Корпус'), {
            'fields': (
                'body',
                'weight',
                ('pneumatic_connection', 'pneumatic_connection_thread', 'cable_glands_holes'),
                ('body_material', 'body_material_specified'),
                ('sealing_material_specified',),
                ('solenoid_body_material', 'solenoid_body_material_specified'),
            ),
        }),
        (_('Рабочие параметры'), {
            'fields': (
                ('pressure_min', 'pressure_max'),
                ('work_temp_min', 'work_temp_max'),
                'medium_density_max',
            ),
        }),
        (_('Электрические характеристики'), {
            'fields': (
                'power_supply',
                ('power_consumption_start', 'power_consumption_hot', 'power_consumption_hold'),
            ),
        }),
        (_('Изображения и документация'), {
            'fields': ('image_gallery', 'tech_docs'),
        }),
        (_('Настройки отображения'), {
            'fields': ('sorting_order', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'body', 'function', 'actuation',
            'manual_override', 'power_supply', 'producer', 'brand',
            'body_material', 'sealing_material_specified',
            'solenoid_body_material', 'solenoid_body_material_specified',
            'body_material_specified', 'ip', 'exd',
            'pneumatic_connection', 'pneumatic_connection_thread',
            'cable_glands_holes',
        )
