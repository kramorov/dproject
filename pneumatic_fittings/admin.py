# pneumatic_fittings/admin.py
from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminStructuredDataMixinCopyMixin
from core.admin_template_placeholders import TemplatePlaceholdersAdminMixin
from .models import PneumaticFittingVariety, PneumaticFitting, PneumaticFittingModelLine, FittingShape, \
    FittingFixationMethod


@admin.register(PneumaticFittingVariety)
class PneumaticFittingVarietyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'fixation_method', 'shape', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description', 'fixation_method', 'shape')
        }),
        (_('Настройки отображения'), {
            'fields': ('sorting_order', 'is_active')
        }),
    )


class PneumaticFittingForm(forms.ModelForm):
    class Meta:
        model = PneumaticFitting
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(
                attrs={'size': 80, 'style': 'width: 80%', 'placeholder': 'Введите название фитинга'}),
            'code': forms.TextInput(attrs={'size': 30, 'style': 'width: 50%'}),
            'description': forms.Textarea(attrs={'rows': 6, 'cols': 80, 'style': 'width: 90%'}),
        }


@admin.register(PneumaticFitting)
class PneumaticFittingAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    form = PneumaticFittingForm
    list_display = [
        'name', 'code', 'equipment_type', 'model_line__brand', 'image_gallery',
        'pipe_diameter', 'thread', 'thread_inner_outer', 'sorting_order', 'is_active'
    ]
    list_editable = ['code', 'pipe_diameter', 'thread', 'sorting_order', 'is_active']
    list_filter = [
        'equipment_type', 'model_line__brand', 'model_line__code', 'fitting_variety',
        'body_material', 'pipe_material', 'pipe_diameter', 'thread', 'thread_inner_outer'
    ]
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ('tech_docs',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', ('code', 'fitting_variety', 'model_line'),
                        ('body_material',),
                        ('pipe_material', 'pipe_diameter'), ('thread', 'thread_inner_outer'),
                        ('pressure_min', 'pressure_max'),
                        ('description', 'sorting_order', 'is_active'))
        }),
        (_('Изображения и документация'), {
            'fields': ('image_gallery', 'tech_docs'),
        }),
        (_('Номенклатура (SKU)'), {
            'fields': ('sku',),
            'classes': ('collapse',),
        }),
        (_('Температура'), {
            'fields': ('temp_min', 'temp_max'),
        }),
    )

    silencer_fieldset = (
        _('Для глушителей'),
        {'fields': (('flow_rate', 'noise_level', 'operating_pressure'))},
    )

    def get_fieldsets(self, request, obj=None):
        """Глушительные поля показываем только у глушителей (вид = тип оборудования)."""
        fieldsets = list(self.fieldsets)
        is_silencer = (
            obj is not None
            and obj.equipment_type_id is not None
            and obj.equipment_type.code == 'fitting-silencer'
        )
        if is_silencer:
            fieldsets.insert(1, self.silencer_fieldset)
        return fieldsets

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'fitting_variety',
            'body_material', 'pipe_material', 'thread', 'equipment_type'
        )

    actions = ['copy_selected_fittings']

    def copy_selected_fittings(self, request, queryset):
        """Action для копирования выбранных фитингов"""
        copied_count = 0
        for fitting in queryset:
            copy_obj = fitting.copy()
            copy_obj.save()
            copied_count += 1
        self.message_user(request, f'Успешно скопировано {copied_count} фитинг(ов)')

    copy_selected_fittings.short_description = "Копировать выбранные фитинги"


class PneumaticFittingModelLineForm(forms.ModelForm):
    class Meta:
        model = PneumaticFittingModelLine
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'size': 80, 'style': 'width: 80%', 'placeholder': 'Введите текст названия серии'
            }),
            'name_template': forms.Textarea(attrs={
                'rows': 3, 'cols': 80, 'style': 'width: 90%; height: 80px;',
                'placeholder': 'Введите шаблон для текстового названия фитинга'
            }),
            'description_template': forms.Textarea(attrs={
                'rows': 3, 'cols': 80, 'style': 'width: 90%; height: 80px;',
                'placeholder': 'Введите шаблон для описания фитинга'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3, 'cols': 80, 'style': 'width: 90%', 'placeholder': 'Введите описание'
            }),
        }


@admin.register(PneumaticFittingModelLine)
class PneumaticFittingModelLineAdmin(TemplatePlaceholdersAdminMixin, AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    template_item_model = PneumaticFitting
    form = PneumaticFittingModelLineForm
    list_display = [
        'name', 'code', 'brand', 'is_swivel',
        'sorting_order', 'is_active'
    ]
    list_editable = ['sorting_order', 'is_active']
    list_filter = [
        'brand',
    ]
    filter_horizontal = ('tech_docs', 'cert_docs')

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', ('code', 'equipment_type'),
                        ('producer', 'brand', 'is_swivel'),
                        'name_template',
                        'description_template',
                        'description', ('sorting_order', 'is_active'))
        }),
        (_('Изображения и документация'), {
            'fields': ('image_gallery', 'tech_docs', 'cert_docs'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'producer', 'brand',
        )

    actions = ['copy_selected_fitting_model_line']

    def copy_selected_fitting_model_line(self, request, queryset):
        """Action для копирования выбранных фитингов"""
        copied_count = 0
        for fitting in queryset:
            copy_obj = fitting.copy(save_copy=False)
            copy_obj.save()
            copied_count += 1
        self.message_user(request, f'Успешно скопировано {copied_count} фитинг(ов)')

    copy_selected_fitting_model_line.short_description = "Копировать выбранные серии"


@admin.register(FittingShape)
class FittingShapeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'sorting_order', 'is_active')
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'is_active', 'sorting_order')
        }),
        ('Описания', {
            'fields': ('description', 'help_text_content'),
            'classes': ('collapse',),
        }),
    )


@admin.register(FittingFixationMethod)
class FittingFixationMethodAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'sorting_order', 'is_active')
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ('sorting_order', 'name')
