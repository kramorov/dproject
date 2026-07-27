from django.db import models


class CascadeRule(models.Model):
    """Правило каскада параметров от родительского типа оборудования к дочернему.

    При выборе продукта в родительском узле дерева подбора, фактические
    характеристики выбранного продукта пробрасываются в фильтры дочернего
    узла согласно mapping.

    Пример:
        parent_type = actuator, child_type = solenoid
        mapping = {
            "port_size_npt": "connection_size",
            "namur_interface": "mounting_type",
            "air_consumption_nl": "flow_rate"
        }

    При выборе привода ABRA-DA-150-F12 с port_size_npt="G1/4" и namur_interface=true,
    в дочерний узел solenoid добавится:
        cascade_params = {"connection_size": "G1/4", "mounting_type": "namur"}
    """

    parent_type = models.ForeignKey(
        "core.EquipmentType", on_delete=models.CASCADE, related_name="ai_cascade_rules_from",
        help_text="Родительский тип (откуда берём параметры)"
    )
    child_type = models.ForeignKey(
        "core.EquipmentType", on_delete=models.CASCADE, related_name="ai_cascade_rules_to",
        help_text="Дочерний тип (куда пробрасываем параметры)"
    )
    mapping = models.JSONField(
        help_text=(
            'Маппинг: {"поле_родителя": "поле_дочернего_фильтра", ...}. '
            "Ключ — имя поля в спецификации родительского продукта, "
            "значение — имя поля в фильтре дочернего узла."
        )
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cascade Rule"
        verbose_name_plural = "Cascade Rules"
        unique_together = [("parent_type", "child_type")]

    def __str__(self):
        return f"{self.parent_type.code} → {self.child_type.code}"
