# project_customers/models/favorite_brand.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class FavoriteBrand(models.Model):
    """
    Любимый бренд пользователя с приоритетом сортировки.
    Подмножество видимых брендов организации.
    """
    user = models.ForeignKey(
        'ProjectCustomerUser',
        on_delete=models.CASCADE,
        related_name='favorite_brands',
        verbose_name=_("Пользователь")
    )
    brand = models.ForeignKey(
        'producers.Brands',
        on_delete=models.CASCADE,
        related_name='favored_by_users',
        verbose_name=_("Бренд")
    )
    priority = models.IntegerField(
        default=0,
        verbose_name=_("Приоритет"),
        help_text=_("Чем меньше число, тем выше в списке")
    )

    class Meta:
        verbose_name = _("Любимый бренд")
        verbose_name_plural = _("Любимые бренды")
        unique_together = [['user', 'brand']]
        ordering = ['priority', 'brand__name']

    def __str__(self):
        return f"{self.user.get_full_name()} → {self.brand.name}"
