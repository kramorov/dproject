#project_customers/models/customer_settings.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerSettings(models.Model) :
    """
    Общие настройки для клиента
    """
    customer = models.OneToOneField(
        'ProjectCustomer' ,
        on_delete=models.CASCADE ,
        related_name='settings' ,
        verbose_name=_("Клиент")
    )

    # Настройки нумерации
    request_number_template = models.CharField(
        max_length=100 ,
        default="{year}-{seq:04d}" ,
        verbose_name=_("Шаблон номера заявки")
    )
    request_prefix = models.CharField(max_length=20 , blank=True , verbose_name=_("Префикс заявки"))
    request_suffix = models.CharField(max_length=20 , blank=True , verbose_name=_("Суффикс заявки"))

    # Счетчик заявок
    last_request_seq = models.IntegerField(default=0 , verbose_name=_("Последний номер заявки"))
    last_request_year = models.IntegerField(null=True , blank=True)
    last_request_month = models.IntegerField(null=True , blank=True)

    # Интеграции (будут дорабатываться)
    bitrix_webhook = models.CharField(max_length=500 , blank=True , verbose_name=_("Bitrix webhook"))
    onec_api_url = models.CharField(max_length=500 , blank=True , verbose_name=_("1C API URL"))

    class Meta :
        verbose_name = _("Настройки клиента")
        verbose_name_plural = _("Настройки клиентов")

    def __str__(self) :
        return f"Настройки {self.customer.name}"

