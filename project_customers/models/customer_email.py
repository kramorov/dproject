# project_customers/models/customer_email.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerEmail(models.Model):
    """
    Email-адреса организации для разных типов уведомлений
    (заявки, счета, техподдержка).
    """
    EMAIL_TYPE_CHOICES = [
        ('requests', _('Заявки')),
        ('invoices', _('Счета')),
        ('support', _('Техподдержка')),
    ]

    customer = models.ForeignKey(
        'ProjectCustomer',
        on_delete=models.CASCADE,
        related_name='notification_emails',
        verbose_name=_("Организация")
    )
    email_type = models.CharField(
        max_length=30,
        choices=EMAIL_TYPE_CHOICES,
        verbose_name=_("Тип уведомлений")
    )
    email = models.EmailField(
        verbose_name=_("Email")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен")
    )

    class Meta:
        verbose_name = _("Email для уведомлений")
        verbose_name_plural = _("Email-адреса для уведомлений")
        unique_together = [['customer', 'email_type', 'email']]

    def __str__(self):
        return f"{self.customer.name} — {self.get_email_type_display()}: {self.email}"
