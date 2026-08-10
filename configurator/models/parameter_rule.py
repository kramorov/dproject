from django.db import models


class ParameterRule(models.Model):
    """Семантика сравнения параметра — переиспользуемый шаблон.

    Описывает, КАК значение параметра сравнивается с требованием:
    точное совпадение, направленное сравнение, иерархия, группы
    совместимости, подмножество. Также определяет жёсткость (hard/soft)
    и стратегию релаксации для мягких ограничений.

    Один ParameterRule может быть привязан к нескольким equipment_type
    через ParameterBinding. Например, правило "exd" с match_type=hierarchy
    используется для pneumatic-actuator, directional-valve, cable-gland.
    """

    MATCH_TYPE_CHOICES = [
        ("exact", "Точное совпадение"),
        ("directional", "Направленное сравнение"),
        ("hierarchy", "Иерархия"),
        ("compatible", "Группы совместимости"),
        ("subset", "Подмножество"),
        ("composite", "Составное правило"),
    ]

    COMBINE_CHOICES = [
        ("and", "AND — все дочерние правила должны выполниться"),
        ("or", "OR — достаточно выполнения любого дочернего"),
    ]

    HARDNESS_CHOICES = [
        ("hard", "Жёсткое — невыполнение исключает модель"),
        ("soft", "Мягкое — невыполнение даёт штраф"),
    ]

    RELAXATION_CHOICES = [
        ("none", "Не релаксировать"),
        ("step", "Пошагово (шаг из config)"),
        ("percentage", "Процент (шаг из config)"),
        ("compatible", "Соседние группы совместимости"),
        ("any", "Игнорировать ограничение"),
    ]

    code = models.CharField(
        max_length=128,
        unique=True,
        help_text="Уникальный код: temperature_min, exd, thread_size, ip",
    )
    name = models.CharField(max_length=256)

    # ── Семантика сравнения ──
    match_type = models.CharField(
        max_length=16,
        choices=MATCH_TYPE_CHOICES,
        default="exact",
    )
    match_config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Конфигурация сравнения — семантика зависит от match_type:\n"
            '  exact:         {} — не используется\n'
            '  directional:   {"direction": "min"}  — чем меньше, тем лучше\n'
            '                  {"direction": "max"}  — чем больше, тем лучше\n'
            '  hierarchy:     {"levels": ["общепром", "Ex ia", "Ex e", "Exd"]}\n'
            '                  требование уровня N → подходят модели уровня ≥ N\n'
            '  compatible:    {"groups": [["M20", "M20×1.5"], ["G1/4", "G1/4×1.5"]]}\n'
            '  subset:        {"field": "ip_rank"}  — значение модели ⊇ требование'
        ),
    )

    # ── Жёсткость ──
    hardness = models.CharField(
        max_length=8,
        choices=HARDNESS_CHOICES,
        default="soft",
    )

    # ── Релаксация ──
    relaxation_strategy = models.CharField(
        max_length=16,
        choices=RELAXATION_CHOICES,
        default="none",
    )
    relaxation_config = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Конфигурация релаксации:\n"
            '  step:       {"step": 5, "max_steps": 4}  — шаг 5°C, макс 4 шага\n'
            '  percentage: {"percent": 5, "max_steps": 3}  — шаг 5%, макс 3 шага\n'
            '  compatible: {} — перейти к соседним группам\n'
            '  any:        {} — полностью игнорировать'
        ),
    )

    # ── Составное правило ──
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sub_rules",
        help_text="Родительское правило (если это — часть составного composite-правила)",
    )
    combine = models.CharField(
        max_length=4,
        choices=COMBINE_CHOICES,
        null=True,
        blank=True,
        help_text="Как комбинировать sub_rules (только для родительского правила с match_type=composite)",
    )

    priority = models.IntegerField(
        default=0,
        help_text="Приоритет: выше → важнее. Штраф за отклонение = deviation × priority",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "configurator_parameter_rule"
        verbose_name = "Parameter Rule"
        verbose_name_plural = "Parameter Rules"
        ordering = ["code"]

    def __str__(self):
        return f"[{self.code}] {self.name} ({self.match_type}, {self.hardness})"
