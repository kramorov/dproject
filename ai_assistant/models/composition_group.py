# ai_assistant/models/composition_group.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class CompositionGroup(models.Model):
    """Группа композиции — правило объединения типов оборудования в спецификации.

    Определяет, как EquipmentType объединяются в составе изделия:
    - required: обязательный компонент
    - optional: опциональный компонент
    - xor: ровно один из нескольких вариантов

    Поддерживает вложенность: CompositionGroup может содержать другие
    CompositionGroup (через parent self-FK).
    """

    GROUP_TYPE_CHOICES = [
        ("required", _("Обязательный")),
        ("optional", _("Опциональный")),
        ("xor", _("XOR — ровно один из")),
    ]

    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Название"),
        help_text=_("Символьное обозначение группы композиции"),
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Код"),
        help_text=_("Код группы композиции"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки"),
        help_text=_("Порядок сортировки в списке"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Активно свойство или нет"),
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
        verbose_name=_("Родительская группа"),
        help_text=_("Родительская CompositionGroup для вложенности"),
    )


    references = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="referenced_by",
        verbose_name="Ссылки на группы",
        help_text="CompositionGroup, на которые ссылается эта группа (не вложенность)",
    )

    equipment_types = models.ManyToManyField(
        "core.EquipmentType",
        blank=True,
        related_name="composition_groups",
        verbose_name=_("Типы оборудования"),
        help_text=_("EquipmentType, входящие в эту группу"),
    )

    group_type = models.CharField(
        max_length=16,
        choices=GROUP_TYPE_CHOICES,
        default="required",
        verbose_name=_("Тип группы"),
        help_text=_("required / optional / xor"),
    )


    output_schema = models.ForeignKey(
        "JSONSchema", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="composition_groups",
        verbose_name=_("JSON Schema"),
        help_text=_("JSON-схема выходного формата для этой группы (MBOM/подбор)"),
    )

    prompt_template = models.ForeignKey(
        "AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="composition_groups",
        verbose_name=_("Prompt Template"),
        help_text=_("Шаблон промпта для этой группы (MBOM/подбор)"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Создано"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлено"))

    class Meta:
        db_table = "ai_composition_group"
        verbose_name = _("Composition Group")
        verbose_name_plural = _("Composition Groups")
        ordering = ["sorting_order", "name"]

    def __str__(self):
        return self.name or self.code or f"CG #{self.id}"

    def get_descendants_ids(self):
        """Получить ID всех потомков (итеративно, с защитой от циклов)."""
        seen = {self.id}
        level = list(
            CompositionGroup.objects.filter(parent_id=self.id)
            .values_list("id", flat=True)
        )
        result = []
        while level:
            next_level = []
            for child_id in level:
                if child_id in seen:
                    continue
                seen.add(child_id)
                result.append(child_id)
            if result:
                next_level = list(
                    CompositionGroup.objects.filter(parent_id__in=level)
                    .values_list("id", flat=True)
                )
            level = next_level
        return result

    def get_ancestors(self):
        """Получить всех предков (путь от корня)."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
