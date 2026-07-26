from django.conf import settings
from django.db import models


class AIQuerySample(models.Model):
    """Обучающая/тестовая выборка запросов для отладки промптов и регрессионного тестирования.

    Содержит образцы пользовательских запросов с ожидаемой интенцией,
    ожидаемыми фильтрами, категорией и эталонным ответом.
    Используется для валидации качества классификации и регрессионного
    тестирования изменений в шаблонах промптов.
    """

    text = models.TextField()
    expected_intent = models.CharField(max_length=64, null=True, blank=True)
    expected_filters = models.JSONField(null=True, blank=True)
    is_valid = models.BooleanField(default=True)
    category = models.CharField(
        max_length=64,
        choices=[
            ("actuator_selection", "Подбор привода"),
            ("price_check", "Запрос цены"),
            ("replacement", "Замена/аналог"),
            ("specs", "Характеристики"),
            ("general", "Общий"),
        ],
        default="general",
    )
    response_text = models.TextField(null=True, blank=True)
    tree_json = models.JSONField(
        null=True,
        blank=True,
        help_text="Эталонное дерево SelectionNode (для обучения)",
    )
    final_selections_json = models.JSONField(
        null=True,
        blank=True,
        help_text="Эталонные выборы пользователя (для обучения)",
    )
    prompt_template = models.ForeignKey(
        "AIPromptTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="query_samples",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Query Sample"
        verbose_name_plural = "AI Query Samples"
        ordering = ["-created_at"]

    def __str__(self):
        """Человекочитаемое представление образца запроса.

        Returns:
            str: первые 100 символов текста запроса.

        Пример:
            >>> sample = AIQuerySample(text="Подбери привод для задвижки 30с941нж Ду80")
            >>> str(sample)
            'Подбери привод для задвижки 30с941нж Ду80'
        """
        return self.text[:100]
