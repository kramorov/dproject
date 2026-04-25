#project_customers/admin/user_admin.py
from django.contrib import admin
from ..models.user import ProjectCustomerUser


@admin.register(ProjectCustomerUser)
class ProjectCustomerUserAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'customer', 'email', 'is_active']
    list_filter = ['customer', 'is_active']
    search_fields = ['last_name', 'first_name', 'email']