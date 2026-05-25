#project_customers/admin/settings_admin.py
from django.contrib import admin

from project_customers.models import CustomerSettings , UserSettings


@admin.register(CustomerSettings)
class CustomerSettingsAdmin(admin.ModelAdmin):
    list_display = ['customer', 'default_currency', 'request_number_template']
    search_fields = ['customer__name']


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'phone', 'email_notifications']
    search_fields = ['user__last_name', 'user__first_name']
