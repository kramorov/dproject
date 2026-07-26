from django.db import models


class JSONSchema(models.Model):
    """Версионируемая JSON-схема выходного формата для Instructor.

    Отделена от AIPromptTemplate, чтобы:
    - Редактировать схему независимо от текста промпта.
    - Переиспользовать одну схему с разными промптами.
    - Версионировать схемы (v1 → v2 при добавлении полей).

    Используется StepConfig.output_schema для указания ожидаемого
    формата structured output на конкретном шаге конвейера.
    """

    name = models.CharField(
        max_length=128, db_index=True,
        help_text="Имя схемы: 'tree_schema', 'actuator_filters', 'solenoid_filters', ..."
    )
    version = models.CharField(
        max_length=16,
        help_text="Версия: '1', '2', ..."
    )
    description = models.TextField(
        null=True, blank=True,
        help_text="Описание назначения схемы"
    )
    schema_json = models.JSONField(
        help_text=(
            "JSON Schema для Instructor structured output. "
            'Пример: {"type": "object", "properties": {"torque_nm": {"type": "number"}}, '
            '"required": ["torque_nm"]}'
        )
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "JSON Schema"
        verbose_name_plural = "JSON Schemas"
        ordering = ["name", "-version"]
        unique_together = [("name", "version")]

    def __str__(self):
        return f"{self.name} v{self.version}"
