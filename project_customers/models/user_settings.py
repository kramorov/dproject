#project_customers/models/user_settings.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserSettings(models.Model) :
    """
    Индивидуальные настройки пользователя клиента
    """
    user = models.OneToOneField(
        'ProjectCustomerUser' ,
        on_delete=models.CASCADE ,
        related_name='settings' ,
        verbose_name=_("Пользователь")
    )

    # Подписи
    # signature = models.ImageField(upload_to='signatures/' , blank=True , null=True , verbose_name=_("Подпись"))
    signature_text = models.CharField(max_length=500 , blank=True , verbose_name=_("Текст подписи"))

    # Контактные данные (переопределение)
    email = models.EmailField(blank=True , verbose_name=_ ("Email (личный)"))
    phone = models.CharField(max_length=50 , blank=True , verbose_name=_("Телефон (личный)"))

    # Уведомления
    email_notifications = models.BooleanField(default=True , verbose_name=_ ("Email уведомления"))

    class Meta :
        verbose_name = _("Настройки пользователя")
        verbose_name_plural = _("Настройки пользователей")

    def __str__(self) :
        return f"Настройки {self.user.get_full_name()}"