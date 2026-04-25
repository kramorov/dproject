#project_customers/models/user.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class ProjectCustomerUser(models.Model) :
    """
    Пользователь клиента (аккаунт для доступа)
    """
    user = models.OneToOneField(
        User ,
        on_delete=models.CASCADE ,
        related_name='customer_profile' ,
        verbose_name=_("Пользователь Django")
    )

    customer = models.ForeignKey(
        'ProjectCustomer' ,
        on_delete=models.CASCADE ,
        related_name='users' ,
        verbose_name=_("Клиент")
    )

    # Контактные данные
    first_name = models.CharField(max_length=100 , verbose_name=_("Имя"))
    last_name = models.CharField(max_length=100 , verbose_name=_("Фамилия"))
    middle_name = models.CharField(max_length=100 , blank=True , verbose_name=_("Отчество"))

    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(max_length=50 , blank=True , verbose_name=_("Телефон"))

    # Должность
    position = models.CharField(max_length=200 , blank=True , verbose_name=_("Должность"))

    # Дефолтное юридическое лицо (для КП и счетов)
    default_legal_entity = models.ForeignKey(
        'LegalEntity' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        verbose_name=_("Юридическое лицо по умолчанию")
    )

    # Права доступа (пока не используем, оставляем на будущее)
    # role = models.CharField(max_length=50, default='user')

    is_active = models.BooleanField(default=True , verbose_name=_("Активен"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta :
        verbose_name = _("Пользователь клиента")
        verbose_name_plural = _("Пользователи клиентов")

    def __str__(self) :
        return f"{self.last_name} {self.first_name} ({self.customer.name})"

    def get_full_name(self) :
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()