from django.db import models


class ComponentRequirement(models.Model):
    """Требования и результат подбора для одного типа оборудования в сборке.

    Создаётся автоматически при разворачивании CompositionGroup.
    Хранит как требования пользователя (own_requirements), так и
    вычисленные эффективные параметры (effective_requirements),
    каскад от родителя (cascade_params) и результат подбора.
    """

    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("requirements_filled", "Требования заданы"),
        ("filtered", "Варианты получены"),
        ("selected", "Выбран"),
        ("skipped", "Пропущен (optional)"),
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
        help_text="Тип оборудования (null для виртуальных узлов без ET)",
    )
    composition_group_node = models.ForeignKey(
        "ai_assistant.CompositionGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="component_requirements",
        help_text="Узел CompositionGroup, из которого создан этот компонент",
    )

    # ── Дерево ──
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    path = models.CharField(
        max_length=256,
        db_index=True,
        help_text="Materialized path: '1', '1/2', '1/2/1'",
    )
    level = models.IntegerField(default=1)
    order = models.IntegerField(default=0)

    # ── Требования ──
    own_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Что явно указал пользователь/AI для этого компонента",
    )
    effective_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Вычисляемое: global + inherited + derived + own",
    )
    cascade_params = models.JSONField(
        null=True,
        blank=True,
        help_text="Параметры, проброшенные от выбора родительского продукта (DerivationRule)",
    )

    # ── Результат подбора ──
    filter_results = models.JSONField(
        null=True,
        blank=True,
        help_text="Результат API-фильтра: candidate list",
    )
    selected_product_type = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="app_label.ModelName выбранного продукта",
    )
    selected_product_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID выбранного продукта",
    )
    selected_product_specs = models.JSONField(
        null=True,
        blank=True,
        help_text="Фактические характеристики выбранного продукта",
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
        db_table = "configurator_component_requirement"
        verbose_name = "Component Requirement"
        verbose_name_plural = "Component Requirements"
        ordering = ["assembly", "path"]
        constraints = [
            models.UniqueConstraint(
                fields=["assembly", "path"],
                name="uq_component_requirement_assembly_path",
            ),
        ]
        indexes = [
            models.Index(fields=["assembly", "status"]),
            models.Index(fields=["equipment_type", "status"]),
        ]

    def __str__(self):
        et = self.equipment_type.code if self.equipment_type else "?"
        return f"CR#{self.id} [{et}] p={self.path} ({self.status})"
