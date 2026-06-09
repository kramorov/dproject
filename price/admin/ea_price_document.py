# price/admin/ea_price_document.py
from django.contrib import admin
from price.models.ea_price_document import EAPriceDocument


@admin.register(EAPriceDocument)
class EAPriceDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'document_date', 'price_variety', 'currency',
        'model_line',
        'power_supply', 'status', 'is_active',
    ]
    list_filter = ['status', 'is_active']
    search_fields = ['name']
    autocomplete_fields = ['power_supply']
    readonly_fields = ['status']
