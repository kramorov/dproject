# project_customers/models/site_section.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSection(models.Model):
    """
    Раздел сайта, доступный пользователям клиента.
    Справочник — фиксированный набор, управляется через фикстуры.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код раздела"),
        help_text=_("Уникальный код раздела (catalog, configurator, ...)")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Человекочитаемое название раздела")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен"),
        help_text=_("Доступен ли раздел для назначения")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки")
    )

    class Meta:
        verbose_name = _("Раздел сайта")
        verbose_name_plural = _("Разделы сайта")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name
