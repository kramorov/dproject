# common/eav_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from .eav_abstract_models import EAVAttribute, EAVValue


class EAVValueInline(admin.TabularInline):
    """Inline для отображения EAV значений"""
    model = EAVValue
    extra = 1
    fields = ('attribute', 'value', 'value_type', 'is_required', 'display_order')
    verbose_name = _('EAV характеристика')
    verbose_name_plural = _('EAV характеристики')

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Упрощаем queryset для атрибутов
        formset.form.base_fields['attribute'].queryset = EAVAttribute.objects.filter(is_global=True)
        return formset

    def value_type(self, obj):
        return obj.attribute.value_type

    value_type.short_description = _('Тип значения')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('attribute')


class EAVAdminMixin:
    """Mixin для добавления EAV функциональности в админку любой модели"""

    def get_inlines(self, request, obj=None):
        inlines = super().get_inlines(request, obj) or []
        # Добавляем EAV inline только для существующих объектов
        if obj and hasattr(obj, 'eav_values'):
            inlines = list(inlines) + [EAVValueInline]
        return inlines

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Здесь можно добавить логику инициализации EAV атрибутов


@admin.register(EAVAttribute)
class EAVAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'value_type', 'is_global', 'default_value')
    list_filter = ('value_type', 'is_global')
    search_fields = ('name', 'description')
    list_editable = ('is_global',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_global')
        }),
        (_('Значения'), {
            'fields': ('value_type', 'choices', 'default_value')
        }),
    )


@admin.register(EAVValue)
class EAVValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'entity', 'value', 'display_order')
    list_filter = ('attribute', 'attribute__value_type')
    search_fields = ('attribute__name', 'value', 'entity_object_id')
    list_select_related = ('attribute',)
    list_editable = ('display_order',)

    def entity(self, obj):
        return f"{obj.entity_content_type}: {obj.entity_object_id}"

    entity.short_description = _('Сущность')