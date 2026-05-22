# sku/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from rangefilter.filters import DateRangeFilter
from .models import SKU


class SKUResource(resources.ModelResource):
    class Meta:
        model = SKU
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True
        exclude = ('source_content_type', 'source_object_id', 'extra')


@admin.register(SKU)
class SKUAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = SKUResource

    # ── Список ──
    list_display = (
        'id',
        'code',
        'name',
        'equipment_type',
        'brand',
        'description_preview',
        'is_active',
    )
    list_editable = ('code','brand' , 'equipment_type','is_active' ,)
    list_filter = (
        'is_active',
        ('equipment_type', admin.RelatedOnlyFieldListFilter),
        ('brand', admin.RelatedOnlyFieldListFilter),
        ('created_at', DateRangeFilter),
    )
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    list_per_page = 50
    list_select_related = ('equipment_type', 'brand')


    # ── Форма редактирования ──
    fieldsets = (
        (None, {
            'fields': (
                ('code', 'is_active'),
                'name',
                'description',
                ('equipment_type', 'brand'),
            )
        }),
        (_('Источник'), {
            'fields': ('source_content_type', 'source_object_id', 'source_link', 'extra'),
            'classes': ('collapse',),
            'description': _('Модель оборудования, из которой создана эта запись SKU'),
        }),
    )
    readonly_fields = (
        'source_content_type', 'source_object_id',
        'source_link',
        'created_at', 'updated_at',
    )

    # ── Отображаемые поля ──

    @admin.display(description=_('Описание'))
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:80] + '…' if len(obj.description) > 80 else obj.description
        return '—'

    @admin.display(description=_('Модель-источник'))
    def source_link(self, obj):
        if obj.source_content_type and obj.source_object_id:
            ct = obj.source_content_type
            try:
                obj_instance = ct.get_object_for_this_type(pk=obj.source_object_id)
                admin_url = reverse(
                    f'admin:{ct.app_label}_{ct.model}_change',
                    args=[obj.source_object_id]
                )
                return format_html(
                    '<a href="{}">{} #{}</a>',
                    admin_url, ct.model, obj.source_object_id
                )
            except Exception:
                return f'{ct.model} #{obj.source_object_id}'
        return '—'
