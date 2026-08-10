from django.db import models


class FittingPattern(models.Model):
    """Шаблон фитингов для контекста монтажа.

    В отличие от PropagationRule и DerivationRule, не передаёт значения
    параметров между существующими компонентами — создаёт НОВЫЕ
    ComponentRequirement для фитингов.

    Контекст монтажа (condition) определяет, какой шаблон применить:
    - Соленоид 5/2 NAMUR на приводе → 2 прямых + 1 угловой фитинг
    - Соленоид 5/2 отдельно стоящий → 5 прямых фитингов
    - Позиционер NAMUR → 2 угловых + скоба
    """

    code = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=256)

    applies_to = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.CASCADE,
        related_name="fitting_patterns",
        help_text="К какому типу оборудования относится шаблон",
    )

    condition = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Условие срабатывания шаблона. Примеры:\n"
            '  {"valve_function": ["5/2", "5/3"], "mounting": "namur_on_actuator"}\n'
            '  {"valve_function": ["5/2"], "mounting": "standalone"}\n'
            '  {"mounting": "namur_on_actuator"}  — любой function_type'
        ),
    )

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "configurator_fitting_pattern"
        verbose_name = "Fitting Pattern"
        verbose_name_plural = "Fitting Patterns"
        ordering = ["applies_to", "code"]

    def __str__(self):
        return f"[{self.code}] {self.name}"

    def matches(self, context: dict) -> bool:
        """Проверяет, подходит ли шаблон под контекст монтажа."""
        for key, expected in self.condition.items():
            actual = context.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True


class FittingPatternItem(models.Model):
    """Одна позиция фитинга в шаблоне."""

    pattern = models.ForeignKey(
        "FittingPattern",
        on_delete=models.CASCADE,
        related_name="items",
    )
    equipment_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.PROTECT,
        related_name="fitting_pattern_items",
        help_text="Тип оборудования для этой позиции (fitting-thread-pipe, mk-...)",
    )
    quantity = models.IntegerField(
        default=1,
        help_text="Количество фитингов этого типа",
    )

    config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Конфигурация фитинга:\n"
            '  {"angle": "straight", "size_from": "parent.port_size_npt"} — прямой, размер от привода\n'
            '  {"angle": "angled_90", "size_from": "parent.port_size_npt"} — угловой 90°\n'
            '  {"purpose": "bracket"} — скоба/кронштейн (не фитинг)'
        ),
    )

    order = models.IntegerField(default=0)

    class Meta:
        db_table = "configurator_fitting_pattern_item"
        verbose_name = "Fitting Pattern Item"
        verbose_name_plural = "Fitting Pattern Items"
        ordering = ["pattern", "order"]

    def __str__(self):
        eq = self.equipment_type.code if self.equipment_type else "?"
        return f"{self.pattern.code}: {self.quantity}×{eq} (order={self.order})"
