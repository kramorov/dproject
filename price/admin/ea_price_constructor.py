# price/admin/ea_price_constructor.py
from django.contrib import admin
from price.models.ea_price_constructor import EAPriceConstructor


@admin.register(EAPriceConstructor)
class EAPriceConstructorAdmin(admin.ModelAdmin):
    list_display = [
        'model_line_item', 'power_supply', 'option_field',
        'option_id', 'surcharge', 'price_variety', 'is_active',
    ]
    list_filter = ['price_variety', 'is_active', 'option_field']
    list_editable = ['surcharge', 'is_active']
    search_fields = ['option_field']
    autocomplete_fields = ['model_line_item', 'power_supply']
