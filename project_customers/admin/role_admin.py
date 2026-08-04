# project_customers/admin/role_admin.py
from django.contrib import admin
from ..models.role import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'customer', 'is_default', 'sorting_order']
    list_filter = ['customer', 'is_default']
    search_fields = ['name', 'code', 'customer__name']
    filter_horizontal = ['section_permissions']
    fieldsets = [
        (None, {'fields': ['customer', 'name', 'code', 'is_default', 'sorting_order']}),
        ('Права', {'fields': ['section_permissions']}),
    ]
