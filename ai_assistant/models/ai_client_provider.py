from django.db import models


class AIClientProvider(models.Model):
    """Конфигурация AI-провайдера клиента (мультитенантность, будущее).

    Хранит настройки подключения к внешнему AI-провайдеру
    (DeepSeek, OpenAI или произвольный custom-эндпоинт) для каждого клиента.
    Позволяет в будущем гибко переключать провайдеров на уровне тенанта.
    """

    customer = models.ForeignKey(
        "project_customers.ProjectCustomer",
        on_delete=models.CASCADE,
        related_name="ai_providers",
    )
    provider_type = models.CharField(
        max_length=32,
        choices=[("deepseek", "DeepSeek"), ("openai", "OpenAI"), ("custom", "Custom")],
        default="deepseek",
    )
    api_url = models.URLField()
    api_key = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Client Provider"
        verbose_name_plural = "AI Client Providers"

    def __str__(self):
        """Человекочитаемое представление провайдера.

        Returns:
            str: строка вида ``<customer>: <provider_type>``.

        Пример:
            >>> provider = AIClientProvider(customer="ООО Ромашка", provider_type="deepseek")
            >>> str(provider)
            'ООО Ромашка: deepseek'
        """
        return f"{self.customer}: {self.provider_type}"
