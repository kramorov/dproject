# pneumatic_fittings/admin.py
from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminStructuredDataMixinCopyMixin
from core.admin_template_placeholders import TemplatePlaceholdersAdminMixin
from core.admin_regenerate_items import RegenerateSeriesItemsAdminMixin
from .models import (
    PneumaticFitting, PneumaticSilencer, PneumaticPlug,
    PneumaticFittingModelLine, PneumaticSilencerModelLine, PneumaticPlugModelLine,
    FittingShape, FittingFixationMethod,
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


class _BaseFittingItemAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ('tech_docs',)
    list_display = [
        'name', 'code', 'equipment_type', 'model_line__brand', 'image_gallery',
        'thread', 'thread_inner_outer', 'sorting_order', 'is_active'
    ]
    list_editable = ['code', 'thread', 'sorting_order', 'is_active']
    actions = ['copy_selected_fittings']

    def copy_selected_fittings(self, request, queryset):
        copied_count = 0
        for fitting in queryset:
            copy_obj = fitting.copy()
            copy_obj.save()
            copied_count += 1
        self.message_user(request, f'Успешно скопировано {copied_count} объект(ов)')

    copy_selected_fittings.short_description = "Копировать выбранные позиции"


@admin.register(PneumaticFitting)
class PneumaticFittingAdmin(_BaseFittingItemAdmin):
    form = PneumaticFittingForm
    list_display = [
        'name', 'code', 'equipment_type', 'model_line__brand', 'image_gallery',
        'pipe_diameter', 'thread', 'thread_inner_outer', 'sorting_order', 'is_active'
    ]
    list_editable = ['code', 'pipe_diameter', 'thread', 'sorting_order', 'is_active']
    list_filter = [
        'equipment_type', 'model_line__brand', 'model_line__code',
        'model_line__shape', 'model_line__fixation_method',
        'body_material', 'pipe_material', 'pipe_diameter', 'thread', 'thread_inner_outer'
    ]

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', ('code', 'model_line'),
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'model_line__shape', 'model_line__fixation_method',
            'body_material', 'pipe_material', 'thread', 'equipment_type'
        )


@admin.register(PneumaticSilencer)
class PneumaticSilencerAdmin(_BaseFittingItemAdmin):
    list_filter = [
        'equipment_type', 'model_line__brand', 'model_line__code',
        'body_material', 'thread', 'thread_inner_outer'
    ]

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', ('code', 'model_line'),
                        ('body_material',),
                        ('thread', 'thread_inner_outer'),
                        ('flow_rate', 'noise_level', 'operating_pressure'),
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'body_material', 'thread', 'equipment_type'
        )


@admin.register(PneumaticPlug)
class PneumaticPlugAdmin(_BaseFittingItemAdmin):
    list_filter = [
        'equipment_type', 'model_line__brand', 'model_line__code',
        'body_material', 'thread', 'thread_inner_outer'
    ]

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', ('code', 'model_line'),
                        ('body_material',),
                        ('thread', 'thread_inner_outer'),
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'body_material', 'thread', 'equipment_type'
        )


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
class PneumaticFittingModelLineAdmin(RegenerateSeriesItemsAdminMixin, TemplatePlaceholdersAdminMixin, AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    template_item_model = PneumaticFitting
    regenerate_items_related_name = 'pneumaticfitting_items'
    form = PneumaticFittingModelLineForm
    list_display = [
        'name', 'code', 'shape', 'fixation_method', 'brand', 'is_swivel',
        'sorting_order', 'is_active'
    ]
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['brand', 'shape', 'fixation_method']
    filter_horizontal = ('tech_docs', 'cert_docs')

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', ('code', 'equipment_type'),
                        ('shape', 'fixation_method'),
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
            'producer', 'brand', 'shape', 'fixation_method',
        )

    actions = ['copy_selected_fitting_model_line']

    def copy_selected_fitting_model_line(self, request, queryset):
        copied_count = 0
        for fitting in queryset:
            copy_obj = fitting.copy(save_copy=False)
            copy_obj.save()
            copied_count += 1
        self.message_user(request, f'Успешно скопировано {copied_count} фитинг(ов)')

    copy_selected_fitting_model_line.short_description = "Копировать выбранные серии"


@admin.register(PneumaticSilencerModelLine)
class PneumaticSilencerModelLineAdmin(RegenerateSeriesItemsAdminMixin, TemplatePlaceholdersAdminMixin, AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    template_item_model = PneumaticSilencer
    regenerate_items_related_name = 'pneumaticsilencer_items'
    list_display = ['name', 'code', 'brand', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['brand']
    filter_horizontal = ('tech_docs', 'cert_docs')

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', ('code', 'equipment_type'),
                        ('producer', 'brand'),
                        'name_template',
                        'description_template',
                        'description', ('sorting_order', 'is_active'))
        }),
        (_('Изображения и документация'), {
            'fields': ('image_gallery', 'tech_docs', 'cert_docs'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('producer', 'brand')


@admin.register(PneumaticPlugModelLine)
class PneumaticPlugModelLineAdmin(RegenerateSeriesItemsAdminMixin, TemplatePlaceholdersAdminMixin, AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    template_item_model = PneumaticPlug
    regenerate_items_related_name = 'pneumaticplug_items'
    list_display = ['name', 'code', 'brand', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['brand']
    filter_horizontal = ('tech_docs', 'cert_docs')

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', ('code', 'equipment_type'),
                        ('producer', 'brand'),
                        'name_template',
                        'description_template',
                        'description', ('sorting_order', 'is_active'))
        }),
        (_('Изображения и документация'), {
            'fields': ('image_gallery', 'tech_docs', 'cert_docs'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('producer', 'brand')


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
