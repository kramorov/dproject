#project_customers/admin/customer_admin.py
from django.contrib import admin
from ..models.customer import ProjectCustomer


@admin.register(ProjectCustomer)
class ProjectCustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'is_active', 'access_until', 'email']
    list_filter = ['is_active']
    search_fields = ['name', 'short_name', 'email']