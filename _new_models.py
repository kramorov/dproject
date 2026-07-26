"""New models to append to ai_assistant/models.py."""

NEW_MODELS = r"""

# ─────────────────────────────────────────────────────────────────
# Новые модели: конфигурируемый конвейер подбора (2026-07-26)
# ─────────────────────────────────────────────────────────────────

class EquipmentType(models.Model):
    """Справочник типов оборудования.

    Определяет, какие виды оборудования участвуют в подборе,
    их типичный уровень вложенности, семантику параметров
    и API-эндпоинт для фильтрации.
    """

    code = models.CharField(max_length=64, unique=True, db_index=True)
    label = models.CharField(max_length=128)
    level = models.IntegerField(default=1, help_text="Типичный уровень вложенности (1=позиция, 2=компонент, ...)")
    param_semantics = models.JSONField(
        default=dict, blank=True,
        help_text='Семантика параметров: {"torque_nm": {"direction": "min", "label": "не менее"}, ...}'
    )
    filter_endpoint = models.CharField(
        max_length=256, null=True, blank=True,
        help_text="API-эндпоинт для вызова фильтров (POST /api/...)"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Equipment Type"
        verbose_name_plural = "Equipment Types"
        ordering = ["level", "code"]

    def __str__(self):
        return f"{self.label} ({self.code})"


class JSONSchema(models.Model):
    """Версионируемая JSON-схема выходного формата.

    Используется Instructor для структурированного вывода LLM.
    Независима от промпта — можно менять схему, не трогая промпт.
    """

    name = models.CharField(max_length=128, db_index=True)
    version = models.CharField(max_length=16)
    description = models.TextField(null=True, blank=True)
    schema_json = models.JSONField(help_text="JSON Schema для Instructor structured output")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "JSON Schema"
        verbose_name_plural = "JSON Schemas"
        ordering = ["name", "-version"]
        unique_together = [("name", "version")]

    def __str__(self):
        return f"{self.name} v{self.version}"


class StepConfig(models.Model):
    """Конфигурация шага конвейера.

    Связывает шаг (decompose/extract/filter/...) и тип оборудования
    с конкретным промптом, JSON-схемой и ролью ИИ-модели.
    """

    STEP_CHOICES = [
        ("decompose", "Decompose — текст → дерево"),
        ("extract", "Extract — дерево → фильтры"),
        ("filter", "Filter — фильтры → варианты"),
        ("select", "Select — выбор + каскад"),
        ("compare", "Compare — требования vs факт"),
        ("format", "Format — EBOM + результат"),
    ]

    step = models.CharField(max_length=32, choices=STEP_CHOICES, db_index=True)
    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.CASCADE, null=True, blank=True,
        related_name="step_configs",
        help_text="Тип оборудования (null = общий, для decompose)"
    )
    prompt_template = models.ForeignKey(
        "AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="step_configs",
        help_text="Промпт для этого шага"
    )
    output_schema = models.ForeignKey(
        JSONSchema, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="step_configs",
        help_text="JSON-схема выхода (Instructor)"
    )
    model_role = models.CharField(
        max_length=32, default="extraction",
        help_text="Роль модели из AIProvider.model_mapping (classification/extraction/debug)"
    )
    priority = models.IntegerField(default=10, help_text="Приоритет (меньше = выше)")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Step Config"
        verbose_name_plural = "Step Configs"
        ordering = ["step", "priority"]
        unique_together = [("step", "equipment_type")]

    def __str__(self):
        eq = self.equipment_type.code if self.equipment_type else "*"
        return f"{self.step} / {eq}"


class StepConfigOverride(models.Model):
    """Пользовательское переопределение конфигурации шага.

    Позволяет клиенту использовать другую модель, промпт или схему
    для конкретного шага/оборудования.
    """

    customer = models.ForeignKey(
        "project_customers.ProjectCustomer", on_delete=models.CASCADE,
        related_name="step_overrides"
    )
    step_config = models.ForeignKey(
        StepConfig, on_delete=models.CASCADE, related_name="overrides"
    )
    prompt_template = models.ForeignKey(
        "AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", help_text="Другой промпт (null = дефолтный)"
    )
    prompt_suffix = models.TextField(
        null=True, blank=True,
        help_text="Добавка в конец промпта (например, «Учитывай только продукцию ABRA»)"
    )
    model_role = models.CharField(
        max_length=32, null=True, blank=True,
        help_text="Другая роль модели (null = дефолтная)"
    )
    output_schema = models.ForeignKey(
        JSONSchema, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", help_text="Другая схема (null = дефолтная)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Step Config Override"
        verbose_name_plural = "Step Config Overrides"
        unique_together = [("customer", "step_config")]

    def __str__(self):
        return f"{self.customer} → {self.step_config}"


class CascadeRule(models.Model):
    """Правило каскада параметров от родительского типа к дочернему.

    При выборе продукта в родительском узле параметры выбранного продукта
    пробрасываются в фильтры дочернего узла согласно mapping.
    """

    parent_type = models.ForeignKey(
        EquipmentType, on_delete=models.CASCADE, related_name="cascade_rules_from"
    )
    child_type = models.ForeignKey(
        EquipmentType, on_delete=models.CASCADE, related_name="cascade_rules_to"
    )
    mapping = models.JSONField(
        help_text='Маппинг полей: {"port_size_npt": "connection_size", "namur_interface": "mounting_type"}'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cascade Rule"
        verbose_name_plural = "Cascade Rules"
        unique_together = [("parent_type", "child_type")]

    def __str__(self):
        return f"{self.parent_type.code} → {self.child_type.code}"


class SelectionNode(models.Model):
    """Узел дерева подбора.

    Представляет одну позицию или компонент в дереве подбора.
    Хранит результаты всех пройденных шагов: decompose, extract,
    filter, compare. Поддерживает вложенность через parent (self-FK).
    """

    TASK_CHOICES = [
        ("selection", "Подбор оборудования"),
        ("price_check", "Запрос цены"),
        ("cert_search", "Поиск сертификата"),
        ("specs", "Характеристики"),
        ("general", "Общий"),
    ]

    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("decomposed", "Декомпозирован"),
        ("extracting", "Извлечение..."),
        ("extracted", "Параметры извлечены"),
        ("filtering", "Подбор..."),
        ("filtered", "Варианты получены"),
        ("selected", "Выбран вариант"),
        ("compared", "Сравнение готово"),
        ("needs_info", "Нужны уточнения"),
        ("error", "Ошибка"),
    ]

    UNIT_CHOICES = [
        ("pcs", "шт"),
        ("m", "м"),
        ("kg", "кг"),
        ("set", "комплект"),
        ("lot", "партия"),
    ]

    conversation = models.ForeignKey(
        AIConversation, on_delete=models.CASCADE, related_name="selection_nodes"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="selection_nodes"
    )
    task_type = models.CharField(
        max_length=32, choices=TASK_CHOICES, default="selection", db_index=True
    )

    # Позиционирование в дереве
    level = models.IntegerField(default=1, db_index=True)
    order = models.IntegerField(default=0)
    path = models.CharField(max_length=256, db_index=True, help_text="Materialized path: «1/2/3»")
    label = models.CharField(max_length=256, help_text="Человекочитаемая метка: «Пневмопривод DA, 150Нм»")

    # Количество
    quantity = models.FloatField(default=1.0)
    quantity_unit = models.CharField(max_length=8, choices=UNIT_CHOICES, default="pcs")

    # ── Шаг 1-2: исходные требования (НЕИЗМЕННЫ после extract) ──
    decompose_output = models.JSONField(null=True, blank=True, help_text="Сырой вывод decompose для узла")
    extract_output = models.JSONField(null=True, blank=True, help_text="Структурированные фильтры из исходных требований")

    # ── Каскад (добавляется от родителя при select) ──
    cascade_params = models.JSONField(null=True, blank=True, help_text="Параметры от выбора родителя")

    # ── Шаг 3-4: подбор ──
    filter_output = models.JSONField(null=True, blank=True, help_text="Результат API-фильтра: {options, total}")
    selected_product_type = models.CharField(max_length=128, null=True, blank=True)
    selected_product_id = models.IntegerField(null=True, blank=True)
    selected_product_specs = models.JSONField(null=True, blank=True, help_text="Фактические характеристики продукта")

    # ── Шаг 5: сравнение ──
    compare_output = models.JSONField(null=True, blank=True, help_text="[{param, required, actual, match, note}]")

    # Статус
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending", db_index=True)
    status_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Selection Node"
        verbose_name_plural = "Selection Nodes"
        ordering = ["conversation", "level", "order"]
        indexes = [
            models.Index(fields=["conversation", "path"]),
            models.Index(fields=["conversation", "status"]),
            models.Index(fields=["equipment_type", "status"]),
        ]

    def __str__(self):
        eq = f"[{self.equipment_type.code}]" if self.equipment_type else ""
        return f"Node#{self.id} L{self.level} {eq} {self.label[:60]}"

    @property
    def effective_params(self) -> dict:
        """Эффективные параметры: исходные требования + каскад от родителя.

        Используется при вызове API-фильтров. Каскадные параметры
        имеют приоритет над исходными требованиями.
        """
        result = dict(self.extract_output or {})
        if self.cascade_params:
            result.update(self.cascade_params)
        return result

    @property
    def total_quantity(self) -> float:
        """Итоговое количество с учётом родителей.

        Произведение quantity по всей цепочке от корня до узла.
        """
        qty = self.quantity
        node = self.parent
        while node:
            qty *= node.quantity
            node = node.parent
        return qty
"""


def append_models():
    path = r'ai_assistant\models.py'
    with open(path, 'a', encoding='utf-8') as f:
        f.write(NEW_MODELS)
    print('New models appended to models.py')


if __name__ == '__main__':
    append_models()
