from django.db import models


class Company(models.Model):
    symbolic_code = models.CharField(max_length=200, help_text='Рабочее название компании')
    company_name = models.CharField(max_length=500, help_text='Официальное название компании (для документов)')

    def __str__(self):
        return self.symbolic_code


class CompanyPerson(models.Model):
    symbolic_code = models.CharField(max_length=200, help_text='ФИО сотрудника')
    employee_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employee_company',
                                         help_text='Компания сотрудника')
    phone_number_office = models.CharField(max_length=15, blank=True, null=True,
                                           help_text='Телефон сотрудника офисный (городской)')
    phone_number_cell = models.CharField(max_length=15, blank=True, null=True, help_text='Телефон сотрудника сотовый')
    person_email = models.EmailField(max_length=255, blank=True, null=True, help_text='Email сотрудника')

    def __str__(self):
        return self.symbolic_code
