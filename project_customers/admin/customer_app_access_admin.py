# project_customers/admin/customer_app_access_admin.py
from django.contrib import admin
from ..models.customer_app_access import CustomerAppAccess


@admin.register(CustomerAppAccess)
class CustomerAppAccessAdmin(admin.ModelAdmin):
    list_display = ['customer', 'app', 'brand_filter', 'is_active']
    list_filter = ['is_active', 'brand_filter', 'app']
    search_fields = ['customer__name', 'app__name']
    filter_horizontal = ['brands']
