from django.db import models

from .ai_message import AIMessage


class AITokenUsage(models.Model):
    """Учёт потреблённых токенов на каждое сообщение.

    Связан один-к-одному с AIMessage. Фиксирует модель LLM,
    количество токенов промпта, completion и reasoning,
    общее число токенов и оценочную стоимость запроса.
    """

    message = models.OneToOneField(
        AIMessage,
        on_delete=models.CASCADE,
        related_name="token_usage",
    )
    model = models.CharField(max_length=64)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    reasoning_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = "AI Token Usage"
        verbose_name_plural = "AI Token Usages"

    def __str__(self):
        """Человекочитаемое представление использования токенов.

        Returns:
            str: строка вида ``Tokens: <total_tokens> (<model>) — $<cost>``.
            Если оценка стоимости отсутствует, выводится ``N/A``.

        Пример:
            >>> usage = AITokenUsage(model="deepseek-chat", total_tokens=1523, cost_estimate=0.0021)
            >>> str(usage)
            'Tokens: 1523 (deepseek-chat) — $0.002100'
        """
        cost = f"${self.cost_estimate:.6f}" if self.cost_estimate is not None else "N/A"
        return f"Tokens: {self.total_tokens} ({self.model}) — {cost}"
