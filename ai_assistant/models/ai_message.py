from django.db import models

from .ai_conversation import AIConversation


class AIMessage(models.Model):
    """Одно сообщение в диалоге: от пользователя, LLM, классификатора или оркестратора.

    Хранит текст сообщения, структурированное содержимое (JSON),
    ссылку на использованный шаблон промпта, определённую интенцию,
    уверенность классификатора, latency и информацию об ошибках.
    Поддерживает древовидную структуру через self-ссылающийся parent.
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant (LLM)"),
        ("classifier", "Classifier"),
        ("orchestrator", "Orchestrator"),
        ("system", "System"),
    ]

    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, db_index=True)
    content = models.TextField()
    structured_content = models.JSONField(null=True, blank=True)
    prompt_used = models.TextField(null=True, blank=True)
    prompt_template = models.ForeignKey(
        "AIPromptTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )
    intent = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    confidence = models.FloatField(null=True, blank=True)
    schema_name = models.CharField(max_length=64, null=True, blank=True)
    reasoning = models.TextField(null=True, blank=True)
    context_summary = models.TextField(null=True, blank=True)  # саммари контекста на момент сообщения
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "AI Message"
        verbose_name_plural = "AI Messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["intent"]),
        ]

    def __str__(self):
        """Человекочитаемое представление сообщения.

        Returns:
            str: строка вида ``Msg#<id> [<role>] <первые 80 символов content>``.

        Пример:
            >>> msg = AIMessage(id=7, role="user", content="Подбери привод для задвижки Ду80")
            >>> str(msg)
            'Msg#7 [user] Подбери привод для задвижки Ду80'
        """
        return f"Msg#{self.id} [{self.role}] {self.content[:80]}"
