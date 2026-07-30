# sku/models/mbom.py
"""MBOM — Manufacturing Bill of Materials (производственная спецификация).

Иерархический список выбранных продуктов (SKU) с группировкой по
CompositionGroup и EquipmentType.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class MBOM(models.Model):
    """Производственная спецификация (Manufacturing BOM).

    Создаётся на основе AIConversation (результат AI-подбора) или вручную.
    Содержит иерархический набор MBOMItem.
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_("Название"),
        help_text=_("Название спецификации"),
    )
    code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код MBOM"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
    )

    conversation = models.ForeignKey(
        "ai_assistant.AIConversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mboms",
        verbose_name=_("Сессия AI-подбора"),
        help_text=_("Связанная сессия AI-ассистента (если создана через подбор)"),
    )

    customer = models.ForeignKey(
        "project_customers.ProjectCustomer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mboms",
        verbose_name=_("Клиент проекта"),
        help_text=_("Привязка к клиенту (null = системная спецификация)"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mboms",
        verbose_name=_("Пользователь"),
        help_text=_(
            "Приватная спецификация пользователя (null = общая/клиентская)"
        ),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Создано"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлено"))

    class Meta:
        db_table = "sku_mbom"
        verbose_name = _("MBOM (Спецификация)")
        verbose_name_plural = _("MBOM (Спецификации)")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or self.code or f"MBOM #{self.id}"


class MBOMItem(models.Model):
    """Элемент производственной спецификации.

    Представляет одну позицию в MBOM: тип оборудования + выбранный SKU +
    количество. Поддерживает иерархию через parent self-FK.
    """

    mbom = models.ForeignKey(
        MBOM,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Спецификация"),
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
        verbose_name=_("Родительский элемент"),
        help_text=_("Родительский элемент для иерархии"),
    )

    equipment_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="mbom_items",
        verbose_name=_("Тип оборудования"),
    )

    composition_group = models.ForeignKey(
        "ai_assistant.CompositionGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mbom_items",
        verbose_name=_("Composition Group"),
        help_text=_("Группа композиции, к которой относится элемент"),
    )

    sku = models.ForeignKey(
        "sku.SKU",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="mbom_items",
        verbose_name=_("SKU"),
        help_text=_("Выбранная номенклатурная позиция"),
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name=_("Количество"),
    )

    quantity_unit = models.CharField(
        max_length=32,
        default="шт",
        blank=True,
        verbose_name=_("Ед. изм."),
    )

    position = models.IntegerField(
        default=0,
        verbose_name=_("Позиция"),
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_("Примечания"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sku_mbom_item"
        verbose_name = _("Элемент MBOM")
        verbose_name_plural = _("Элементы MBOM")
        ordering = ["mbom", "position"]

    def __str__(self):
        eq = self.equipment_type.code if self.equipment_type else "?"
        sku_code = self.sku.code if self.sku else "—"
        return f"[{eq}] {sku_code} ×{self.quantity}"
