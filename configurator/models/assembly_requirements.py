from django.db import models


class AssemblyRequirements(models.Model):
    """Контейнер сессии подбора — одна запись = одна сборка.

    Независим от AI — может быть создан вручную или из AIConversation.
    composition_group определяет структуру (какие типы оборудования входят),
    root_node — точка входа для навигации (позволяет начать подбор с любой
    ветки CompositionGroup, например только «ФР со скобой»).
    """

    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("in_progress", "В подборе"),
        ("done", "Завершён"),
    ]

    name = models.CharField(max_length=256, blank=True, default="")
    composition_group = models.ForeignKey(
        "ai_assistant.CompositionGroup",
        on_delete=models.PROTECT,
        related_name="assemblies",
        help_text="Шаблон сборки (pa-kit, ea-kit, ...)",
    )
    root_node = models.ForeignKey(
        "ai_assistant.CompositionGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entry_point_assemblies",
        help_text="Точка входа — если указана, дерево обрезается до этой ветки",
    )

    # Глобальные требования — применяются ко всем компонентам сборки
    global_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Общие требования: temperature_min, exd, pressure, ...",
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )

    # Связь с AI (опционально — для будущей интеграции)
    conversation = models.ForeignKey(
        "ai_assistant.AIConversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assemblies",
        help_text="Сессия AI, если подбор инициирован через LLM",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "configurator_assembly_requirements"
        verbose_name = "Assembly Requirements"
        verbose_name_plural = "Assembly Requirements"
        ordering = ["-created_at"]

    def __str__(self):
        name = self.name or f"Assembly #{self.id}"
        cg = self.composition_group.code if self.composition_group else "?"
        return f"{name} [{cg}]"
