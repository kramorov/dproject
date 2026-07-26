from django.db import models


class AIConversation(models.Model):
    """Диалог / цепочка запросов пользователя.

    Представляет одну сессию общения пользователя с AI-ассистентом.
    Объединяет все сообщения в рамках одного диалога, отслеживает
    статус обработки, определённую интенцию и источник обращения.

    Атрибуты класса:
        INCOMING: входящий запрос, ожидает обработки.
        PROCESSING: запрос в процессе обработки.
        COMPLETED: обработка успешно завершена.
        TIMEOUT: превышено время ожидания ответа.
        ERROR: ошибка при обработке запроса.
    """

    INCOMING = "incoming"
    PROCESSING = "processing"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"

    STATUS_CHOICES = [
        (INCOMING, "Incoming"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (TIMEOUT, "Timeout"),
        (ERROR, "Error"),
    ]

    customer = models.ForeignKey(
        "project_customers.ProjectCustomer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_conversations",
    )
    session_key = models.CharField(max_length=64, db_index=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=INCOMING, db_index=True)
    intent = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    source = models.CharField(
        max_length=32,
        choices=[
            ("web_form", "Web Form"),
            ("email", "Email"),
            ("messenger", "Messenger"),
            ("api", "External API"),
        ],
        default="web_form",
    )
    selection_tree = models.JSONField(
        null=True,
        blank=True,
        help_text="Кеш полного дерева SelectionNode для быстрой отдачи на фронт",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Conversation"
        verbose_name_plural = "AI Conversations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self):
        """Человекочитаемое представление диалога.

        Returns:
            str: строка вида ``Conv#<id> [<intent>] <status>``.
            Если интенция не определена, выводится ``?``.

        Пример:
            >>> conv = AIConversation(id=42, intent="actuator_selection", status="completed")
            >>> str(conv)
            'Conv#42 [actuator_selection] completed'
        """
        return f"Conv#{self.id} [{self.intent or '?'}] {self.status}"
