from django.db import models


class PipelineSkill(models.Model):
    """Скилл конвейера подбора — связывает шаг, тип оборудования, промпт и схему.

    Skill = что делать (step) + для чего (equipment_type) + как (prompt) + в каком формате (output_schema).

    Разрешение конфигурации:
    1. Ищем SkillOverride для клиента.
    2. Если нет — берём дефолтный PipelineSkill.
    3. Если нет PipelineSkill для пары (step, equipment_type) — шаг пропускается.

    Примеры:
        decompose / *        → decode v2, tree_schema v1, model=debug
        extract / actuator   → extract_actuator v1, actuator_filters v1, model=extraction
        extract / solenoid   → extract_solenoid v1, solenoid_filters v1, model=extraction
        filter / actuator    → (без ИИ), endpoint из EquipmentType
    """

    STEP_CHOICES = [
        ("decompose", "Decompose — текст → дерево"),
        ("extract", "Extract — дерево → фильтры"),
        ("filter", "Filter — фильтры → варианты"),
        ("select", "Select — выбор + каскад"),
        ("compare", "Compare — требования vs факт"),
        ("format", "Format — EBOM + результат"),
    ]

    code = models.CharField(
        max_length=64, unique=True, null=True, blank=True, db_index=True,
        help_text=(
            "Уникальный код скилла. Используется для ссылки на PipelineSkill "
            "из кода вместо поиска по паре (step, equipment_type). "
            "Пример: 'decompose_default', 'extract_actuator', 'extract_solenoid'."
        )
    )

    step = models.CharField(
        max_length=32, choices=STEP_CHOICES, db_index=True,
        help_text="Шаг конвейера"
    )
    equipment_type = models.ForeignKey(
        "core.EquipmentType", on_delete=models.CASCADE, null=True, blank=True,
        related_name="ai_step_configs",
        help_text="Тип оборудования (null = общий, для decompose)"
    )
    prompt_template = models.ForeignKey(
        "AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="step_configs",
        help_text="Промпт для этого шага (null = без ИИ, как filter)"
    )
    output_schema = models.ForeignKey(
        "JSONSchema", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="step_configs",
        help_text="JSON-схема выхода для Instructor (null = без structured output)"
    )
    model_role = models.CharField(
        max_length=32, default="extraction",
        help_text="Роль модели из AIProvider.model_mapping: 'classification', 'extraction', 'debug'"
    )
    priority = models.IntegerField(
        default=10,
        help_text="Приоритет (меньше = выше). Используется при нескольких конфигах на один шаг."
    )
    avg_latency_ms = models.IntegerField(
        null=True, blank=True,
        help_text=(
            "Скользящее среднее времени отклика LLM для этого скилла (мс). "
            "Рассчитывается по последним 5 запросам. Используется для оценки "
            "времени ожидания на фронте."
        )
    )
    latency_sample_count = models.IntegerField(
        default=0,
        help_text="Количество замеров, использованных для расчёта avg_latency_ms",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pipeline Skill"
        verbose_name_plural = "Pipeline Skills"
        ordering = ["step", "priority"]
        unique_together = [("step", "equipment_type")]

    def __str__(self):
        eq = self.equipment_type.code if self.equipment_type else "*"
        return f"{self.step} / {eq}"
