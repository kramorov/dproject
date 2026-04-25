#project_customers/admin/legal_entity_admin.py
from django.contrib import admin
from ..models.legal_entity import LegalEntity


@admin.register(LegalEntity)
class LegalEntityAdmin(admin.ModelAdmin):
    list_display = ['short_name', 'customer', 'inn', 'is_default', 'is_active']
    list_filter = ['customer', 'is_default', 'is_active']
    search_fields = ['short_name', 'full_name', 'inn']