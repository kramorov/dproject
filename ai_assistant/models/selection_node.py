from django.db import models


class SelectionNode(models.Model):
    """Узел дерева подбора — центральная структура данных всего конвейера.

    Представляет одну позицию или компонент в дереве подбора.
    Поддерживает вложенность через parent (self-FK) и materialized path.
    Хранит результаты ВСЕХ пройденных шагов в JSON-полях.

    Жизненный цикл узла (status):
        pending → decomposed → extracting → extracted →
        filtering → filtered → selected → compared → done

    Поля по шагам:
    - decompose_output: результат Фазы 1 (decompose) — сырой вывод LLM для узла.
    - extract_output:   результат Фазы 2 (extract) — структурированные фильтры.
                         НЕИЗМЕННЫ после extract. База для поиска замены.
    - cascade_params:   параметры от выбора родителя (Фаза 4 — select).
    - filter_output:    результат Фазы 3 (filter) — список вариантов от API.
    - selected_product_*: выбор пользователя.
    - compare_output:   результат Фазы 5 (compare) — сравнение требований и факта.

    Количество:
    - quantity + quantity_unit — количество для данного узла.
    - total_quantity (property) — итоговое с учётом цепочки родителей.
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
        "AIConversation", on_delete=models.CASCADE, related_name="selection_nodes",
        help_text="Сессия/диалог, в рамках которого ведётся подбор"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children",
        help_text="Родительский узел в дереве (null = корень — позиция)"
    )
    equipment_type = models.ForeignKey(
        "EquipmentType", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="selection_nodes",
        help_text="Тип оборудования (null для узла-контейнера без собственного подбора)"
    )
    task_type = models.CharField(
        max_length=32, choices=TASK_CHOICES, default="selection", db_index=True,
        help_text="Тип задачи: подбор, запрос цены, поиск сертификата, ..."
    )

    # ── Позиционирование в дереве ──
    level = models.IntegerField(
        default=1, db_index=True,
        help_text="Уровень вложенности: 1=позиция, 2=компонент, 3=субкомпонент, ..."
    )
    order = models.IntegerField(
        default=0,
        help_text="Порядок среди siblings"
    )
    path = models.CharField(
        max_length=256, db_index=True,
        help_text="Materialized path: '1', '1/1', '1/1/2', ... — для быстрой навигации по дереву"
    )
    label = models.CharField(
        max_length=256,
        help_text="Человекочитаемая метка: «Пневмопривод DA, 150Нм»"
    )

    # ── Количество ──
    quantity = models.FloatField(
        default=1.0,
        help_text="Количество для данного узла"
    )
    quantity_unit = models.CharField(
        max_length=8, choices=UNIT_CHOICES, default="pcs",
        help_text="Единица измерения: шт, м, кг, комплект, партия"
    )

    # ── Шаг 1: Decompose ──
    decompose_output = models.JSONField(
        null=True, blank=True,
        help_text="Сырой вывод decompose-промпта для данного узла"
    )

    # ── Шаг 2: Extract (НЕИЗМЕННЫ — база для переподбора замены) ──
    extract_output = models.JSONField(
        null=True, blank=True,
        help_text="Структурированные фильтры из исходных требований пользователя. НЕИЗМЕННЫ после extract."
    )

    # ── Каскад от родителя (добавляется при select родителя) ──
    cascade_params = models.JSONField(
        null=True, blank=True,
        help_text="Параметры, проброшенные от выбора родительского продукта через CascadeRule"
    )

    # ── Шаг 3: Filter ──
    filter_output = models.JSONField(
        null=True, blank=True,
        help_text="Результат API-фильтра: {'options': [...], 'total': 20}"
    )

    # ── Шаг 4: Select ──
    selected_product_type = models.CharField(
        max_length=128, null=True, blank=True,
        help_text="Тип выбранного продукта (app_label.ModelName)"
    )
    selected_product_id = models.IntegerField(
        null=True, blank=True,
        help_text="ID выбранного продукта"
    )
    selected_product_specs = models.JSONField(
        null=True, blank=True,
        help_text="Фактические характеристики выбранного продукта (загружаются при select)"
    )

    # ── Шаг 5: Compare ──
    compare_output = models.JSONField(
        null=True, blank=True,
        help_text=(
            "Сравнение требований и факта: "
            "[{'param': 'IP', 'required': 'IP54', 'actual': 'IP67', 'match': True, 'note': 'выше требуемого'}]"
        )
    )

    # ── Статус ──
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    status_message = models.TextField(
        null=True, blank=True,
        help_text="Сообщение о статусе (ошибка, причина needs_info)"
    )

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

        Используется при вызове API-фильтров (Фаза 3).
        Каскадные параметры имеют приоритет над extract_output —
        они уточняют подбор на основе выбора родителя.

        Returns:
            dict: объединённый словарь параметров для передачи в API.
        """
        result = dict(self.extract_output or {})
        if self.cascade_params:
            result.update(self.cascade_params)
        return result

    @property
    def total_quantity(self) -> float:
        """Итоговое количество с учётом всей цепочки родителей.

        Произведение quantity от корня до текущего узла.
        Используется при формировании EBOM/MBOM.

        Returns:
            float: итоговое количество (например, 2 комплекта × 1 шт = 2).
        """
        qty = self.quantity
        node = self.parent
        while node:
            qty *= node.quantity
            node = node.parent
        return qty
