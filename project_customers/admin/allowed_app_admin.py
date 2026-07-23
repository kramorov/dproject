# project_customers/admin/allowed_app_admin.py
from django.contrib import admin
from ..models.allowed_app import AllowedApp


@admin.register(AllowedApp)
class AllowedAppAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'has_brand_filter', 'is_active', 'sorting_order']
    list_filter = ['is_active', 'has_brand_filter']
    search_fields = ['code', 'name']
    list_editable = ['has_brand_filter', 'is_active', 'sorting_order']
