from django.conf import settings
from django.db import models


class AssemblyRequirements(models.Model):
    """Сборка — результат подбора (структура + требования + выбор).

    Жизненный цикл: draft → fixed. Изменения — fork() (полная копия).

    Две линии версионирования:
      - требования: requirement_version → ClientRequestItem.parent_version;
      - состав: parent_assembly (только внутри одной версии требований).
    """

    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("fixed", "Зафиксирована"),
    ]

    name = models.CharField(max_length=256, blank=True, default="")

    # ── Связь с требованиями ──
    requirement_version = models.ForeignKey(
        "client_requests.ClientRequestItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assemblies",
        help_text="Версия требований, которую удовлетворяет сборка (null у шаблона)",
    )

    # ── Структура ──
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

    global_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Общие требования: temperature_min, exd, pressure, ...",
    )

    # ── Жизненный цикл ──
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    revision = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Итерация состава внутри одной версии требований",
    )
    parent_assembly = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_assemblies",
        help_text="Состав-линия: предыдущая сборка под теми же требованиями",
    )
    is_template = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Типовая/каталожная сборка",
    )

    # ── Фиксация ──
    fixed_at = models.DateTimeField(null=True, blank=True)
    fixed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fixed_assemblies",
    )
    fixation_comment = models.TextField(blank=True, default="")

    # ── Связь с AI (опционально) ──
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
        db_table = "assemblies_assembly"
        verbose_name = "Assembly"
        verbose_name_plural = "Assemblies"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["is_template"]),
            models.Index(fields=["requirement_version", "status"]),
        ]

    def __str__(self):
        name = self.name or f"Assembly #{self.id}"
        cg = self.composition_group.code if self.composition_group else "?"
        return f"{name} [{cg}]"
