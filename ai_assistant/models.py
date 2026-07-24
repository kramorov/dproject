from django.db import models
from django.conf import settings


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

    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name="messages")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, db_index=True)
    content = models.TextField()
    structured_content = models.JSONField(null=True, blank=True)
    prompt_used = models.TextField(null=True, blank=True)
    prompt_template = models.ForeignKey(
        "AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True, related_name="messages",
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


class AITokenUsage(models.Model):
    """Учёт потреблённых токенов на каждое сообщение.

    Связан один-к-одному с AIMessage. Фиксирует модель LLM,
    количество токенов промпта, completion и reasoning,
    общее число токенов и оценочную стоимость запроса.
    """

    message = models.OneToOneField(AIMessage, on_delete=models.CASCADE, related_name="token_usage")
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


class AIClientProvider(models.Model):
    """Конфигурация AI-провайдера клиента (мультитенантность, будущее).

    Хранит настройки подключения к внешнему AI-провайдеру
    (DeepSeek, OpenAI или произвольный custom-эндпоинт) для каждого клиента.
    Позволяет в будущем гибко переключать провайдеров на уровне тенанта.
    """

    customer = models.ForeignKey(
        "project_customers.ProjectCustomer", on_delete=models.CASCADE, related_name="ai_providers",
    )
    provider_type = models.CharField(
        max_length=32, choices=[("deepseek", "DeepSeek"), ("openai", "OpenAI"), ("custom", "Custom")],
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
    prompt_template = models.ForeignKey(
        "AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True, related_name="query_samples",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
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
    schema_json = models.JSONField(null=True, blank=True, help_text="JSON Schema для structured output (Instructor)")
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
        help_text='{"classification": "deepseek-chat", "extraction": "deepseek-v4-flash", "debug": "deepseek-v4-pro"}'
    )
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "AI Provider"
        verbose_name_plural = "AI Providers"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {'✅' if self.is_active else '❌'}"
