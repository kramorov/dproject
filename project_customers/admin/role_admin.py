# project_customers/admin/role_admin.py
from django.contrib import admin
from ..models.role import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'customer', 'get_django_user', 'is_default', 'sorting_order']
    list_filter = ['customer', 'is_default']
    search_fields = ['name', 'code', 'customer__name']
    filter_horizontal = ['section_permissions']
    raw_id_fields = ['django_user']
    fieldsets = [
        (None, {'fields': ['customer', 'name', 'code', 'is_default', 'sorting_order']}),
        ('Права', {'fields': ['section_permissions']}),
        ('Django User', {'fields': ['django_user'],
                         'description': 'Общий для всех с этой ролью. Один на роль.'}),
    ]

    def get_django_user(self, obj):
        if obj.django_user:
            return obj.django_user.username
        return '—'
    get_django_user.short_description = 'Django User'
