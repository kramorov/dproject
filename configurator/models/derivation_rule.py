from django.db import models


class DerivationRule(models.Model):
    """Каскад параметров от выбранной модели к зависимым типам оборудования.

    Срабатывает после выбора продукта в родительском компоненте.
    Берёт значение из поля БД-модели продукта и записывает в параметр
    требований дочернего типа.

    Примеры:
        actuator.port_size_npt → solenoid.connection_size
        actuator.thread_size → cable_gland.thread_size
        actuator.mounting_flange → mk-iso.flange_size
    """

    code = models.CharField(max_length=128, unique=True)

    source_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.CASCADE,
        related_name="derivations_from",
        help_text="Тип-источник (откуда берём значение)",
    )
    source_product_field = models.CharField(
        max_length=128,
        help_text=(
            "Поле в БД-модели продукта. Например, у модели PA "
            "есть поле port_size_npt — его значение пойдёт в target"
        ),
    )

    target_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.CASCADE,
        related_name="derivations_to",
        help_text="Тип-приёмник (куда пробрасываем значение)",
    )
    target_param = models.CharField(
        max_length=128,
        help_text=(
            "Имя параметра требований дочернего типа. "
            "Должно совпадать с PropagationRule.param_name для target_type"
        ),
    )

    # Трансформация значения
    transform = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            'null — прямое присваивание. '
            '{"map": {"G1/4": "1/4", "G1/2": "1/2"}} — словарь замены'
        ),
    )

    # Условие срабатывания
    condition = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "null — срабатывает всегда. "
            '{"field": "actuator_variety", "value": "SR"} — только для SR-приводов'
        ),
    )

    priority = models.IntegerField(
        default=0,
        help_text="Приоритет при нескольких правилах на одну пару типов",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "configurator_derivation_rule"
        verbose_name = "Derivation Rule"
        verbose_name_plural = "Derivation Rules"
        ordering = ["source_type", "target_type", "priority"]

    def __str__(self):
        return (
            f"{self.code}: "
            f"{self.source_type.code}.{self.source_product_field}"
            f" → {self.target_type.code}.{self.target_param}"
        )
