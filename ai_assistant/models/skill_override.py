from django.db import models


class SkillOverride(models.Model):
    """Клиентское переопределение скилла (PipelineSkill).

    Позволяет клиенту:
    - Использовать другую ИИ-модель (в т.ч. свою обученную).
    - Подменить промпт (другой шаблон или добавить суффикс).
    - Подменить JSON-схему выхода.

    Приоритет: SkillOverride > PipelineSkill по умолчанию.

    Пример:
        Клиент «Архимед» для extract/filter_regulator:
        - model_role = "custom_fr_model" (своя обученная модель)
        - prompt_suffix = "Учитывай только продукцию ABRA."
    """

    customer = models.ForeignKey(
        "project_customers.ProjectCustomer", on_delete=models.CASCADE,
        related_name="skill_overrides",
        help_text="Клиент, для которого действует переопределение"
    )
    step_config = models.ForeignKey(
        "PipelineSkill", on_delete=models.CASCADE, related_name="overrides",
        help_text="Базовый скилл, который переопределяем"
    )
    prompt_template = models.ForeignKey(
        "AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
        help_text="Другой промпт (null = использовать дефолтный из PipelineSkill)"
    )
    prompt_suffix = models.TextField(
        null=True, blank=True,
        help_text="Текст, добавляемый в конец промпта (например, «Учитывай только продукцию ABRA»)"
    )
    model_role = models.CharField(
        max_length=32, null=True, blank=True,
        help_text="Другая роль модели (null = дефолтная из PipelineSkill)"
    )
    output_schema = models.ForeignKey(
        "JSONSchema", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
        help_text="Другая схема выхода (null = дефолтная)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Skill Override"
        verbose_name_plural = "Skill Overrides"
        unique_together = [("customer", "step_config")]

    def __str__(self):
        return f"{self.customer} → {self.step_config}"
