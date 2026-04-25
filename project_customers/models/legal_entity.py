#project_customers/models/legal_entity.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class LegalEntity(models.Model) :
    """
    Юридическое лицо клиента (может быть несколько)
    """
    customer = models.ForeignKey(
        'ProjectCustomer' ,
        on_delete=models.CASCADE ,
        related_name='legal_entities' ,
        verbose_name=_("Клиент")
    )

    # Реквизиты
    full_name = models.CharField(max_length=300 , verbose_name=_("Полное наименование"))
    short_name = models.CharField(max_length=200 , blank=True , verbose_name=_("Краткое наименование"))
    inn = models.CharField(max_length=20 , verbose_name=_("ИНН"))
    kpp = models.CharField(max_length=20 , blank=True , verbose_name=_("КПП"))
    ogrn = models.CharField(max_length=20 , blank=True , verbose_name=_("ОГРН"))

    # Адрес
    legal_address = models.TextField(blank=True , verbose_name=_("Юридический адрес"))
    postal_address = models.TextField(blank=True , verbose_name=_("Почтовый адрес"))

    # Банковские реквизиты
    bank_name = models.CharField(max_length=200 , blank=True , verbose_name=_("Банк"))
    bik = models.CharField(max_length=20 , blank=True , verbose_name=_("БИК"))
    correspondent_account = models.CharField(max_length=20 , blank=True , verbose_name=_("Корр. счет"))
    checking_account = models.CharField(max_length=20 , blank=True , verbose_name=_("Расчетный счет"))

    # Должности для подписей
    ceo_name = models.CharField(max_length=200 , blank=True , verbose_name=_("ФИО директора"))
    ceo_position = models.CharField(max_length=100 , blank=True , default="Генеральный директор")

    accountant_name = models.CharField(max_length=200 , blank=True , verbose_name=_("ФИО Главный бухгалтер"))
    accountant_position = models.CharField(max_length=100 , blank=True , default="Генеральный директор")

    is_default = models.BooleanField(default=False , verbose_name=_("По умолчанию"))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно"))

    class Meta :
        verbose_name = _("Юридическое лицо")
        verbose_name_plural = _("Юридические лица")

    def __str__(self) :
        return self.short_name or self.full_name[:50]