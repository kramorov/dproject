# project_customers/models/customer_app_access.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerAppAccess(models.Model):
    """
    Разрешение организации на мини-приложение + фильтр по брендам.
    Задаёт потолок: API-ключи не могут расширить этот доступ, только сузить.
    """
    customer = models.ForeignKey(
        'ProjectCustomer',
        on_delete=models.CASCADE,
        related_name='app_access',
        verbose_name=_("Организация")
    )
    app = models.ForeignKey(
        'AllowedApp',
        on_delete=models.CASCADE,
        related_name='customer_access',
        verbose_name=_("Мини-приложение")
    )
    brand_filter = models.CharField(
        max_length=10,
        choices=[('all', _('Все бренды')), ('selected', _('Выбранные бренды'))],
        default='all',
        verbose_name=_("Фильтр брендов")
    )
    brands = models.ManyToManyField(
        'producers.Brands',
        blank=True,
        verbose_name=_("Бренды"),
        help_text=_("Учитывается только при brand_filter='selected'")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно")
    )

    class Meta:
        verbose_name = _("Доступ к мини-приложению")
        verbose_name_plural = _("Доступ к мини-приложениям")
        unique_together = [['customer', 'app']]

    def __str__(self):
        return f"{self.customer.name} → {self.app.name}"

    def save(self, *args, **kwargs):
        """Если brand_filter='all' — очищаем brands при сохранении."""
        if self.brand_filter == 'all':
            # Сначала сохраняем, потом чистим M2M
            super().save(*args, **kwargs)
            self.brands.clear()
        else:
            super().save(*args, **kwargs)
