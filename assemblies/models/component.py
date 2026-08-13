from django.db import models


class ComponentRequirement(models.Model):
    """Узел сборки: тип оборудования + требования + результат подбора.

    `included=False` помечает узел как «не нужен» (status=skipped).
    Базовый тип → selected_sku; составной тип → selected_sku=null (результат в поддереве).
    """

    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("requirements_filled", "Требования заданы"),
        ("filtered", "Варианты получены"),
        ("selected", "Выбран"),
        ("skipped", "Пропущен (не нужен)"),
    ]

    assembly = models.ForeignKey(
        "AssemblyRequirements",
        on_delete=models.CASCADE,
        related_name="components",
    )
    equipment_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="component_requirements",
    )
    composition_group_node = models.ForeignKey(
        "ai_assistant.CompositionGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="component_requirements",
    )

    # ── Дерево ──
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    path = models.CharField(max_length=256, db_index=True, blank=True, default="")
    level = models.IntegerField(default=1)
    order = models.IntegerField(default=0)

    # ── Включение ──
    included = models.BooleanField(
        default=True,
        help_text="Нужен ли узел в сборке (False → status=skipped)",
    )

    # ── Требования ──
    own_requirements = models.JSONField(default=dict, blank=True)
    effective_requirements = models.JSONField(default=dict, blank=True)
    cascade_params = models.JSONField(null=True, blank=True)

    # ── Результат подбора ──
    filter_results = models.JSONField(null=True, blank=True)
    selected_sku = models.ForeignKey(
        "sku.SKU",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="component_requirements",
        help_text="Выбранная номенклатурная позиция (базовый тип)",
    )
    selected_product_specs = models.JSONField(
        null=True,
        blank=True,
        help_text="Фактические характеристики выбранного продукта (снапшот)",
    )

    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assemblies_component"
        verbose_name = "Component Requirement"
        verbose_name_plural = "Component Requirements"
        ordering = ["assembly", "path"]
        constraints = [
            models.UniqueConstraint(
                fields=["assembly", "path"],
                name="uq_component_assembly_path",
            ),
        ]
        indexes = [
            models.Index(fields=["assembly", "status"]),
            models.Index(fields=["equipment_type", "status"]),
        ]

    def __str__(self):
        et = self.equipment_type.code if self.equipment_type else "?"
        return f"CR#{self.id} [{et}] p={self.path} ({self.status})"
