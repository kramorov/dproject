from django.db import models


class AIProvider(models.Model):
    """Конфигурация AI-провайдера (DeepSeek, OpenAI, и т.д.).

    Хранит API-ключ, URL, и JSON-маппинг ролей на модели.
    Активный провайдер используется DeepSeekClient.
    """

    code = models.CharField(max_length=32, unique=True, db_index=True)
    api_key = models.CharField(max_length=512)
    base_url = models.URLField(default="https://api.deepseek.com/v1")
    model_mapping = models.JSONField(
        default=dict,
        help_text='{"classification": "deepseek-chat", "extraction": "deepseek-v4-flash", "debug": "deepseek-v4-pro"}',
    )
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "AI Provider"
        verbose_name_plural = "AI Providers"
        ordering = ["code"]

    def __str__(self):
        """Человекочитаемое представление AI-провайдера.

        Returns:
            str: строка вида ``<code> ✅`` для активного провайдера
            или ``<code> ❌`` для неактивного.

        Пример:
            >>> provider = AIProvider(code="deepseek", is_active=True)
            >>> str(provider)
            'deepseek ✅'
        """
        return f"{self.code} {'✅' if self.is_active else '❌'}"
