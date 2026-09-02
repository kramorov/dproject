# solenoid_valves/admin/dv_model_line_admin.py
from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminStructuredDataMixinCopyMixin
from core.admin_template_placeholders import TemplatePlaceholdersAdminMixin
from solenoid_valves.models import DirectionalValveModelLine
from solenoid_valves.models.dv_model_line_item import DirectionValve


class DirectionalValveModelLineForm(forms.ModelForm):
    """Форма для серии распределительных клапанов"""

    class Meta:
        model = DirectionalValveModelLine
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'size': 80,
                'style': 'width: 80%',
                'placeholder': 'Введите название серии'
            }),
            'code': forms.TextInput(attrs={
                'size': 30,
                'style': 'width: 50%'
            }),
            'name_template': forms.Textarea(attrs={
                'rows': 4,
                'cols': 80,
                'style': 'width: 90%',
                'placeholder': 'Шаблон для генерации названия (например: "Клапан {function} {size}")'
            }),
            'description_template': forms.Textarea(attrs={
                'rows': 4,
                'cols': 80,
                'style': 'width: 90%',
                'placeholder': 'Шаблон для генерации описания'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'cols': 80,
                'style': 'width: 90%'
            }),
        }


@admin.register(DirectionalValveModelLine)
class DirectionalValveModelLineAdmin(TemplatePlaceholdersAdminMixin, AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    """Админка для серии распределительных клапанов (DNA клапана)"""
    template_item_model = DirectionValve
    form = DirectionalValveModelLineForm

    list_display = [
        'name', 'code', 'brand', 'construction', 'operation',
        'working_medium', 'sorting_order', 'is_active'
    ]
    list_editable = ['sorting_order', 'is_active']
    list_filter = [
        'is_active', 'brand', 'construction', 'operation',
        'working_medium', 'solenoid_insulation_class'
    ]
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ('tech_docs', 'cert_docs')

    fieldsets = (
        (_('Основная информация'), {
            'fields': (('name', 'code', 'equipment_type',),'description')
        }),
        (_('Шаблоны генерации'), {
            'fields': ('name_template', 'description_template'),
            'description': _('Шаблоны для автоматической генерации названий и описаний конкретных клапанов')
        }),
        (_('Производитель и бренд'), {
            'fields': ('producer', 'brand'),
            'classes': ('collapse',)
        }),
        (_('Конструктивные характеристики (DNA)'), {
            'fields': (
                'construction',
                'operation',
                'working_medium',
            ),
            'description': _('Эти параметры определяют уникальность серии')
        }),
        (_('Защита и изоляция'), {
            'fields': ('solenoid_insulation_class',),
        }),
        (_('Изображения и документация'), {
            'fields': ('image_gallery', 'tech_docs', 'cert_docs'),
        }),
        (_('Настройки отображения'), {
            'fields': ('sorting_order', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'producer', 'brand', 'construction', 'operation',
            'working_medium'
        )
