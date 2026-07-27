from django.db import models
from .ai_message import AIMessage


class AITokenUsage(models.Model):
    """Token usage per AI message."""
    message = models.OneToOneField(AIMessage, on_delete=models.CASCADE, related_name="token_usage")
    customer = models.ForeignKey(
        "project_customers.ProjectCustomer",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="token_usages",
        help_text="Customer for billing",
    )
    model = models.CharField(max_length=64)
    prompt_tokens = models.IntegerField(default=0, verbose_name="Prompt Tokens")
    completion_tokens = models.IntegerField(default=0, verbose_name="Completion Tokens")
    reasoning_tokens = models.IntegerField(default=0, verbose_name="Reasoning Tokens")
    total_tokens = models.IntegerField(default=0, verbose_name="Total Tokens")
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True, help_text="LLM call latency (ms)")

    class Meta:
        verbose_name = "AI Token Usage"
        verbose_name_plural = "AI Token Usages"
        indexes = [models.Index(fields=["customer", "-id"])]

    def __str__(self):
        c = f"$ {self.cost_estimate:.6f}" if self.cost_estimate is not None else "N/A"
        return f"Tokens: {self.total_tokens} ({self.model}) -- {c}"