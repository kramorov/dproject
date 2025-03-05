from django.contrib import admin
from .models import Company, CompanyPerson

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('symbolic_code', 'company_name')
    search_fields = ('symbolic_code', 'company_name')
    list_filter = ('symbolic_code',)

class CompanyPersonAdmin(admin.ModelAdmin):
    list_display = ('symbolic_code', 'employee_company', 'phone_number_office', 'phone_number_cell', 'person_email')
    search_fields = ('symbolic_code', 'employee_company__symbolic_code', 'person_email')
    list_filter = ('employee_company',)

# Регистрация моделей в админке
admin.site.register(Company, CompanyAdmin)
admin.site.register(CompanyPerson, CompanyPersonAdmin)
