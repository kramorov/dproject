# project_customers/admin/customer_email_admin.py
from django.contrib import admin
from ..models.customer_email import CustomerEmail


@admin.register(CustomerEmail)
class CustomerEmailAdmin(admin.ModelAdmin):
    list_display = ['customer', 'email_type', 'email', 'is_active']
    list_filter = ['is_active', 'email_type']
    search_fields = ['customer__name', 'email']
