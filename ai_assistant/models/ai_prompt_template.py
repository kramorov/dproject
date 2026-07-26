from django.db import models


class AIPromptTemplate(models.Model):
    """Версионируемый шаблон промпта.

    Хранит текст системного промпта с версионированием (name + version).
    Может быть привязан к конкретной интенции и содержать JSON Schema
    для структурированного вывода через Instructor.
    """

    name = models.CharField(max_length=128, db_index=True)
    description = models.TextField(null=True, blank=True)
    template_text = models.TextField()
    version = models.CharField(max_length=16)
    intent = models.CharField(max_length=64, null=True, blank=True)
    schema_name = models.CharField(max_length=64, null=True, blank=True)
    schema_json = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON Schema для structured output (Instructor)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Prompt Template"
        verbose_name_plural = "AI Prompt Templates"
        ordering = ["name", "-version"]
        unique_together = [("name", "version")]

    def __str__(self):
        """Человекочитаемое представление шаблона промпта.

        Returns:
            str: строка вида ``<name> v<version>``.

        Пример:
            >>> tmpl = AIPromptTemplate(name="classifier", version="1.2.0")
            >>> str(tmpl)
            'classifier v1.2.0'
        """
        return f"{self.name} v{self.version}"
