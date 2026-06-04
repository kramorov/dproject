# solenoid_valves/admin/dv_body_admin.py
from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminStructuredDataMixinCopyMixin
from solenoid_valves.models import DirectionValveBody


class DirectionValveBodyForm(forms.ModelForm):
    """Форма для корпуса клапана"""

    class Meta:
        model = DirectionValveBody
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'size': 80,
                'style': 'width: 80%',
                'placeholder': 'Введите название корпуса'
            }),
            'code': forms.TextInput(attrs={
                'size': 30,
                'style': 'width: 50%'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'cols': 80,
                'style': 'width: 90%'
            }),
        }


@admin.register(DirectionValveBody)
class DirectionValveBodyAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    """Админка для корпуса клапана"""
    form = DirectionValveBodyForm

    list_display = [
        'name', 'code', 'brand', 'get_valves_count',
        'sorting_order', 'is_active'
    ]
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['is_active', 'brand']
    search_fields = ['name', 'code', 'brand__name', 'description']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Производитель и бренд'), {
            'fields': ('brand',),
        }),
        (_('Настройки отображения'), {
            'fields': ('sorting_order', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    def get_valves_count(self, obj):
        """Количество клапанов, использующих этот корпус"""
        count = obj.direction_valve_body.count()
        return count if count > 0 else '-'

    get_valves_count.short_description = _('Используется в клапанах')
    get_valves_count.admin_order_field = 'direction_valve_body__count'
