from django.db import models


class StepConfigOverride(models.Model):
    """Пользовательское переопределение конфигурации шага.

    Позволяет клиенту:
    - Использовать другую ИИ-модель (в т.ч. свою обученную).
    - Подменить промпт (другой шаблон или добавить суффикс).
    - Подменить JSON-схему выхода.

    Приоритет: Override > StepConfig по умолчанию.

    Пример:
        Клиент «Архимед» для extract/filter_regulator:
        - model_role = "custom_fr_model" (своя обученная модель)
        - prompt_suffix = "Учитывай только продукцию ABRA."
    """

    customer = models.ForeignKey(
        "project_customers.ProjectCustomer", on_delete=models.CASCADE,
        related_name="step_overrides",
        help_text="Клиент, для которого действует переопределение"
    )
    step_config = models.ForeignKey(
        "StepConfig", on_delete=models.CASCADE, related_name="overrides",
        help_text="Базовая конфигурация, которую переопределяем"
    )
    prompt_template = models.ForeignKey(
        "AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
        help_text="Другой промпт (null = использовать дефолтный из StepConfig)"
    )
    prompt_suffix = models.TextField(
        null=True, blank=True,
        help_text="Текст, добавляемый в конец промпта (например, «Учитывай только продукцию ABRA»)"
    )
    model_role = models.CharField(
        max_length=32, null=True, blank=True,
        help_text="Другая роль модели (null = дефолтная из StepConfig)"
    )
    output_schema = models.ForeignKey(
        "JSONSchema", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
        help_text="Другая схема выхода (null = дефолтная)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Step Config Override"
        verbose_name_plural = "Step Config Overrides"
        unique_together = [("customer", "step_config")]

    def __str__(self):
        return f"{self.customer} → {self.step_config}"
