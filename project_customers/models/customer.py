#project_customers/models/customer.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProjectCustomer(models.Model) :
    """
    Аккаунт клиента (контроль доступа, оплата)
    """
    name = models.CharField(max_length=200 , verbose_name=_("Название"))
    short_name = models.CharField(max_length=100 , blank=True , verbose_name=_("Краткое название"))

    # Доступ
    is_active = models.BooleanField(default=True , verbose_name=_("Активен"))
    access_until = models.DateField(null=True , blank=True , verbose_name=_("Доступ до"))

    # Контакты
    email = models.EmailField(blank=True , verbose_name=_("Email"))
    phone = models.CharField(max_length=50 , blank=True , verbose_name=_("Телефон"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta :
        verbose_name = _("Клиент")
        verbose_name_plural = _("Клиенты")

    def __str__(self) :
        return self.name