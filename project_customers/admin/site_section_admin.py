# project_customers/admin/site_section_admin.py
from django.contrib import admin
from ..models.site_section import SiteSection


@admin.register(SiteSection)
class SiteSectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'sorting_order']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active', 'sorting_order']
