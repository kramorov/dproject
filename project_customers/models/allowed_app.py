# project_customers/models/allowed_app.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class AllowedApp(models.Model):
    """
    Тип мини-приложения для API-доступа (виджеты на сайтах клиентов).
    Справочник — фиксированный набор, управляется через фикстуры.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код приложения"),
        help_text=_("Уникальный код (limit_switch, gearbox, llm_agent, ...)")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Человекочитаемое название мини-приложения")
    )
    has_brand_filter = models.BooleanField(
        default=True,
        verbose_name=_("Фильтр по брендам"),
        help_text=_("Применяется ли фильтрация по брендам (для LLM-агента — False)")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Доступно ли приложение для назначения")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки")
    )

    class Meta:
        verbose_name = _("Мини-приложение (API)")
        verbose_name_plural = _("Мини-приложения (API)")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name
