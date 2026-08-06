# core/models/equipment_type.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import BaseAbstractModel


class EquipmentType(BaseAbstractModel):
    """
    Тип оборудования (классификатор)
    Примеры: 'Пневмопривод', 'Электропривод', 'Клапан', 'Задвижка'
    """
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Родительский тип"),
        help_text=_("Родительский тип оборудования для иерархии")
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Иконка"),
        help_text=_("Иконка для отображения (emoji или название класса CSS)")
    )

    # Связь с моделью товара для цен и документов
    content_type = models.ForeignKey(
        'contenttypes.ContentType', on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_("Модель товара"),
        help_text=_("Django-модель товара этого типа (для цен, документов)")
    )

    # Уровень в иерархии (для удобства)
    level = models.IntegerField(
        default=0,
        verbose_name=_("Уровень иерархии"),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    # ── Шаблон заголовка ──
    title_template = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Шаблон заголовка"),
        help_text=_(
            "Шаблон для generate_title(). Плейсхолдеры: {model_code}, {brand}, "
            "{sensor_variety}, {ip}, {exd}, {work_temp_min}, {work_temp_max}, "
            "{body_material}, {points}, {weight}, и др. из _get_data_dict(). "
            "Оставьте пустым — используется дефолтный шаблон из кода модели."
        )
    )

    # ── AI Assistant: семантика параметров для фазы сравнения ──────────
    param_semantics = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Семантика параметров (AI)"),
        help_text=_(
            "Используется AI Assistant (Фаза 5: compare) для определения направления "
            "сравнения требований пользователя с фактическими характеристиками. "
            "Пример: {\"torque_nm\": {\"direction\": \"min\", \"label\": \"не менее\"}, "
            "\"ip\": {\"direction\": \"min\", \"label\": \"не хуже\"}}. "
            "direction: min (чем больше, тем лучше), max, exact (точное совпадение). "
            "Заполняется только для типов оборудования, участвующих в AI-подборе."
        )
    )

    # ── AI Assistant: API-эндпоинт для фазы фильтрации ──────────────────
    filter_endpoint = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name=_("API-эндпоинт фильтра (AI)"),
        help_text=_(
            "Используется AI Assistant (Фаза 3: filter) — TreeProcessor вызывает этот "
            "эндпоинт для получения списка вариантов оборудования по извлечённым "
            "параметрам. Пример: \"/api/pneumatic_actuators/selector/search/\". "
            "Заполняется только для типов оборудования, участвующих в AI-подборе."
        )
    )


    # ── AI Catalog Schema ──
    ai_title = models.CharField(max_length=200, blank=True, default="", verbose_name="AI title")
    ai_description = models.TextField(blank=True, default="", verbose_name="AI description")
    ai_placeholder = models.CharField(max_length=200, blank=True, default="", verbose_name="AI placeholder")
    ai_hints = models.JSONField(blank=True, default=list, verbose_name="AI hints")

    # ── AI: схема и промпт ──
    output_schema = models.ForeignKey(
        "ai_assistant.JSONSchema", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="equipment_types",
        verbose_name=_("JSON Schema"),
        help_text=_("JSON-схема выходного формата (extract)"),
    )
    prompt_template = models.ForeignKey(
        "ai_assistant.AIPromptTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="equipment_types",
        verbose_name=_("Prompt Template"),
        help_text=_("Шаблон промпта для extract"),
    )

    # ── Мастер подбора ──
    active_selection_wizard = models.ForeignKey(
        'core.SelectionWizard', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='equipment_types',
        verbose_name=_("Активный мастер подбора"),
        help_text=_("Мастер подбора для страницы каталога")
    )

    class Meta:
        db_table = 'core_equipmenttype'
        verbose_name = _("Тип оборудования")
        verbose_name_plural = _("Типы оборудования")
        ordering = ['level', 'sorting_order', 'name']

    def get_descendants_ids(self):
        """Получить ID всех потомков (включая вложенные)"""
        from django.db import connection

        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute("""
                    WITH RECURSIVE descendants AS (
                        SELECT id, parent_id
                        FROM core_equipmenttype
                        WHERE id = %s
                        UNION ALL
                        SELECT child.id, child.parent_id
                        FROM core_equipmenttype child
                        INNER JOIN descendants parent ON child.parent_id = parent.id
                    )
                    SELECT id FROM descendants WHERE id != %s
                """, [self.id, self.id])
                return [row[0] for row in cursor.fetchall()]

        def get_children_ids(parent_id):
            children = EquipmentType.objects.filter(parent_id=parent_id).values_list('id', flat=True)
            result = list(children)
            for child_id in children:
                result.extend(get_children_ids(child_id))
            return result

        return get_children_ids(self.id)

    def get_descendants(self):
        ids = self.get_descendants_ids()
        return EquipmentType.objects.filter(id__in=ids) if ids else EquipmentType.objects.none()

    def get_all_children_ids(self):
        return self.get_descendants_ids()

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
        super().save(*args, **kwargs)

    def get_full_path(self):
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " → ".join(path)

    def get_children_count(self):
        return self.children.count()

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> dict:
        data = super().get_compact_data()
        data.update({
            'level': self.level,
            'parent_id': self.parent_id,
            'content_type_id': self.content_type_id,
            'icon': self.icon,
            'full_path': self.get_full_path(),
            'children_count': self.get_children_count(),
        })
        return data

    def get_display_data(self, view_type: str = 'detail') -> dict:
        if view_type == self.LIST:
            return {
                'id': self.id,
                'name': self.name,
                'code': self.code,
                'level': self.level,
                'full_path': self.get_full_path(),
                'is_active': self.is_active,
                'children_count': self.get_children_count(),
            }

        fields = self._get_base_display_fields()
        fields.update({
            'parent': self._format_foreign_key(
                self.parent,
                label=_("Родительский тип"),
                icon='↕️',
                priority=5,
                include_data='compact'
            ),
            'level': self._format_field(
                self.level,
                'number',
                label=_("Уровень иерархии"),
                icon='📊',
                priority=6
            ),
            'icon': self._format_field(
                self.icon,
                'text',
                label=_("Иконка"),
                icon='🎨',
                priority=7
            ),
            'children': self._format_many_to_many(
                self.children.all(),
                label=_("Дочерние типы"),
                icon='📂',
                priority=8,
                include_data='compact'
            ),
        })

        return {
            'title': self.name,
            'subtitle': f'{self.get_full_path()}',
            'fields': fields,
            'actions': self._get_actions()
        }
