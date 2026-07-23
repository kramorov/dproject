# project_customers/models/role.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """
    Настраиваемая роль пользователя.
    У каждой организации — свой набор ролей.
    """
    customer = models.ForeignKey(
        'ProjectCustomer',
        on_delete=models.CASCADE,
        related_name='roles',
        verbose_name=_("Организация")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название роли")
    )
    code = models.CharField(
        max_length=50,
        verbose_name=_("Код роли"),
        help_text=_("Машинное имя (латиница, без пробелов)")
    )
    section_permissions = models.ManyToManyField(
        'SiteSection',
        blank=True,
        verbose_name=_("Доступ к разделам сайта")
    )
    # Django User — общий для всех пользователей с этой ролью (сессионная обёртка)
    django_user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shared_roles',
        verbose_name=_("Django User роли"),
        help_text=_("Один на роль. Все пользователи с этой ролью логинятся через него.")
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("По умолчанию"),
        help_text=_("Назначается новым пользователям автоматически")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки")
    )

    class Meta:
        verbose_name = _("Роль")
        verbose_name_plural = _("Роли")
        unique_together = [['customer', 'code']]
        ordering = ['sorting_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.customer.name})"

    def save(self, *args, **kwargs):
        # Только одна роль по умолчанию на организацию
        if self.is_default:
            qs = Role.objects.filter(customer=self.customer, is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_default=False)
        super().save(*args, **kwargs)
