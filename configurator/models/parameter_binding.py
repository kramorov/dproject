from django.db import models


class ParameterBinding(models.Model):
    """Привязка ParameterRule к конкретному типу оборудования.

    Один ParameterRule может быть использован для нескольких equipment_type.
    Например, правило "exd" (hierarchy) привязано к pneumatic-actuator,
    directional-valve, cable-gland — у всех поле exd сравнивается одинаково.

    param_name — это имя поля в модели/фильтре оборудования, которое
    может отличаться от code ParameterRule (например, правило "temperature_min"
    привязано как param_name="work_temp_min" в каталоге).
    """

    rule = models.ForeignKey(
        "ParameterRule",
        on_delete=models.CASCADE,
        related_name="bindings",
    )
    equipment_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.CASCADE,
        related_name="parameter_bindings",
    )
    param_name = models.CharField(
        max_length=128,
        help_text="Имя поля в модели/фильтре оборудования",
    )

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "configurator_parameter_binding"
        verbose_name = "Parameter Binding"
        verbose_name_plural = "Parameter Bindings"
        ordering = ["equipment_type", "param_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["equipment_type", "param_name"],
                name="uq_parameter_binding_type_param",
            ),
        ]

    def __str__(self):
        return (
            f"{self.equipment_type.code}.{self.param_name}"
            f" → rule:{self.rule.code}"
        )
