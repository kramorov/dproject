from django.db import models


class PropagationRule(models.Model):
    """Откуда берётся значение параметра для типа оборудования.

    Определяет источник, обязательность и возможность переопределения
    для каждого параметра каждого equipment_type.

    Примеры:
        temperature_min для directional-valve → source=global, нельзя переопределить
        exd для directional-valve → source=global, МОЖНО переопределить (Ex ia)
        torque_nm для pneumatic-actuator → source=user, обязательное
        connection_size для directional-valve → source=derived (из DerivationRule)
    """

    SOURCE_CHOICES = [
        ("user", "Пользователь — должен указать явно"),
        ("global", "Глобальные требования сборки"),
        ("parent", "От родительского компонента в дереве"),
        ("derived", "Вычисляется из выбранной модели — см. DerivationRule"),
    ]

    code = models.CharField(max_length=128, unique=True)
    equipment_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.CASCADE,
        related_name="propagation_rules",
    )
    param_name = models.CharField(
        max_length=128,
        help_text="Имя параметра (temperature_min, exd, voltage, ...)",
    )

    source = models.CharField(max_length=16, choices=SOURCE_CHOICES)
    source_param = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Имя параметра-источника (если source=parent: родительский param_name)",
    )

    # Можно ли переопределить источник значением из own_requirements
    allow_override = models.BooleanField(
        default=True,
        help_text="True — своё значение приоритетнее источника",
    )

    # Обязательность
    is_mandatory = models.BooleanField(
        default=False,
        help_text="True — поле обязательно для заполнения",
    )
    mandatory_condition = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Условие обязательности. null — всегда. "
            '{"param": "actuator_variety", "value": "SR"} — только для SR'
        ),
    )

    priority = models.IntegerField(
        default=0,
        help_text="Приоритет: выше → важнее при scoring и релаксации",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "configurator_propagation_rule"
        verbose_name = "Propagation Rule"
        verbose_name_plural = "Propagation Rules"
        ordering = ["equipment_type", "priority"]
        constraints = [
            models.UniqueConstraint(
                fields=["equipment_type", "param_name"],
                name="uq_propagation_rule_type_param",
            ),
        ]

    def __str__(self):
        return f"{self.code}: {self.equipment_type.code}.{self.param_name} ← {self.source}"
