"""
configurator/models/equipment_type_parameter.py

EquipmentTypeParameter — единая модель параметров для типа оборудования.

Объединяет:
    - FilterDefinition (какие поля есть у типа)
    - PropagationRule (откуда берётся значение)
    - ParameterBinding (как сравнивать)

Один параметр = одна запись. Никаких JSON-блобов, никакого хардкода в коде.
"""

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class EquipmentTypeParameter(models.Model):
    """Параметр типа оборудования — единый источник правды."""

    FIELD_TYPE_CHOICES = [
        ("integer", _("Целое число")),
        ("decimal", _("Десятичное")),
        ("boolean", _("Да/нет")),
        ("choice", _("Выбор из списка")),
        ("fk", _("Foreign Key")),
        ("string", _("Строка")),
    ]

    OPTIONS_SOURCE_CHOICES = [
        ("foreign_key", _("Из связанной модели")),
        ("field_values", _("Уникальные значения поля")),
        ("global_model", _("Из глобального справочника")),
        ("choices", _("Из choices поля")),
        ("custom", _("Кастомный метод")),
    ]

    # ── Идентификация ──
    code = models.CharField(
        max_length=128, blank=True, null=True, unique=True, db_index=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код: 'pa-torque', 'lsb-sensor'. "
                    "Автоматически генерируется если не указан."),
    )
    equipment_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.CASCADE,
        related_name="parameters",
        verbose_name=_("Тип оборудования"),
    )

    # ── Поле в продукте (ContentType + field_path) ──
    product_model = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name=_("Модель продукта"),
        help_text=_("Django-модель продукта: GearBox, DirectionValve, ..."),
    )
    product_model_ref = models.CharField(
        max_length=128, blank=True, null=True,
        verbose_name=_("Ссылка на модель"),
        help_text=_("app_label.ModelName: 'gearbox.GearBox' — fallback без ContentType"),
    )
    field_path = models.CharField(
        max_length=256,
        verbose_name=_("Путь к полю"),
        help_text=_("Путь к полю в модели продукта: 'ip', 'body__max_work_torque'"),
    )

    # ── Отображение ──
    param_name = models.CharField(
        max_length=128,
        verbose_name=_("Имя параметра"),
        help_text=_("Имя в own_requirements: 'ip_id', 'torque_nm'"),
    )
    label = models.CharField(
        max_length=256,
        verbose_name=_("Заголовок"),
        help_text=_("Отображаемое название: 'IP защита', 'Крутящий момент'"),
    )
    field_type = models.CharField(
        max_length=16, choices=FIELD_TYPE_CHOICES, default="choice",
        verbose_name=_("Тип поля"),
    )

    # ── Каталог: FilterDefinition-совместимость ──
    filter_type = models.CharField(
        max_length=32,
        choices=[
            ("exact", "Exact"),
            ("min", "Min"),
            ("max", "Max"),
            ("temp_min", "Temp Min"),
            ("temp_max", "Temp Max"),
            ("ip_rank", "IP Rank"),
            ("exd_compatible", "Exd Compatible"),
            ("choice", "Choice"),
            ("boolean", "Boolean"),
            ("fk_cascade", "FK Cascade"),
            ("thread_compatible", "Thread Compatible"),
        ],
        blank=True, null=True,
        verbose_name=_("Тип фильтра"),
        help_text=_("Какой UI-компонент показать: селект, слайдер, IP-ранг"),
    )
    data_source_type = models.CharField(
        max_length=32,
        choices=[
            ("field_values", "Field Values"),
            ("unique_field_values", "Unique Field Values"),
            ("foreign_key", "Foreign Key"),
            ("global_model", "Global Model"),
            ("choices", "Choices"),
            ("custom", "Custom"),
        ],
        blank=True, null=True,
        verbose_name=_("Источник данных"),
        help_text=_("Откуда брать опции для селектов: FK, глобальная модель, значения поля"),
    )

    # ── Обязательность ──
    is_required = models.BooleanField(
        default=False,
        verbose_name=_("Обязательное"),
        help_text=_("Без этого параметра подбор невозможен (gate)"),
    )
    required_condition = models.JSONField(
        null=True, blank=True,
        verbose_name=_("Условие обязательности"),
        help_text=_('{"param": "actuator_variety_code", "value": "SR"}'),
    )
    priority = models.IntegerField(
        default=0,
        verbose_name=_("Приоритет"),
        help_text=_("Выше = важнее при scoring"),
    )

    # ── Deprecated (будет удалено) ──
    source = models.ForeignKey(
        "ParameterSource",
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name=_("Источник (deprecated)"),
    )
    source_param = models.CharField(max_length=128, blank=True, null=True)
    allow_override = models.BooleanField(default=True)

    # ── Семантика сравнения (бывший ParameterBinding) ──
    parameter_rule = models.ForeignKey(
        "ParameterRule",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="equipment_parameters",
        verbose_name=_("Правило сравнения"),
    )

    # ── Опции для формы ──
    options_source = models.CharField(
        max_length=16, choices=OPTIONS_SOURCE_CHOICES,
        null=True, blank=True,
        verbose_name=_("Источник опций"),
    )
    options_config = models.JSONField(
        null=True, blank=True,
        verbose_name=_("Конфигурация опций"),
        help_text=_('{"model": "params.IpOption", "field": "name", "active_only": true}'),
    )

    # ── Семантика параметра (бывший param_semantics JSON) ──
    param_type = models.CharField(
        max_length=16,
        choices=[
            ("integer", _("Целое число")),
            ("decimal", _("Десятичное")),
            ("boolean", _("Да/нет")),
            ("choice", _("Выбор из списка")),
            ("string", _("Строка")),
        ],
        blank=True, null=True,
        verbose_name=_("Тип значения"),
    )
    unit = models.CharField(
        max_length=64, blank=True, null=True,
        verbose_name=_("Единица измерения"),
        help_text=_("'Нм', '°C', 'бар', 'мм'"),
    )
    description = models.TextField(
        blank=True, null=True,
        verbose_name=_("Описание"),
        help_text=_("Подсказка для AI: что означает этот параметр"),
    )
    enum_values = models.JSONField(
        null=True, blank=True,
        verbose_name=_("Возможные значения"),
        help_text=_("[{\"id\": 1, \"name\": \"Нержавейка\"}, ...] или [\"NPT\", \"BSP\"]"),
    )
    ai_extraction_hint = models.CharField(
        max_length=512, blank=True, null=True,
        verbose_name=_("Подсказка AI для извлечения"),
        help_text=_("'ищи значение в Нм', 'спроси диаметр кабеля'"),
    )

    # ── Служебное ──
    is_active = models.BooleanField(default=True, db_index=True)
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок"))

    class Meta:
        db_table = "configurator_equipment_type_parameter"
        verbose_name = _("Параметр типа оборудования")
        verbose_name_plural = _("Параметры типов оборудования")
        ordering = ["equipment_type", "sorting_order", "param_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["equipment_type", "param_name"],
                name="uq_param_equipment_type_param_name",
            ),
        ]
        indexes = [
            models.Index(fields=["equipment_type", "source"]),
            models.Index(fields=["equipment_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.equipment_type.code}.{self.param_name} ← {self.source.code if self.source else '?'}"

    @property
    def product_model_class(self):
        """Возвращает класс модели продукта (ленивая загрузка)."""
        if self.product_model:
            return self.product_model.model_class()
        if self.product_model_ref:
            from django.apps import apps
            try:
                app_label, model_name = self.product_model_ref.split(".", 1)
                return apps.get_model(app_label, model_name)
            except Exception:
                pass
        return None

    @classmethod
    def generate_json_schema(cls, equipment_type, variant: str = 'ai') -> dict:
        """
        Генерирует JSON Schema для equipment_type из EquipmentTypeParameter.

        Args:
            equipment_type: EquipmentType instance или ID.
            variant: 'ai' — схема для LLM (описания, enum, единицы),
                     'configurator' — схема для формы конфигуратора
                     (source, is_required, allow_override).

        Оба варианта генерируются из одного источника — EquipmentTypeParameter.
        """
        params = cls.objects.filter(
            equipment_type=equipment_type, is_active=True
        ).order_by('sorting_order', 'param_name')

        type_map = {
            'decimal': 'number', 'integer': 'number',
            'choice': 'string', 'string': 'string', 'boolean': 'boolean',
        }

        schema = {"type": "object", "properties": {}, "required": []}
        for p in params:
            prop = {"type": type_map.get(p.param_type, "string")}

            if variant == 'ai':
                # Для AI: что извлечь из текста
                if p.description:
                    prop["description"] = p.description
                if p.enum_values:
                    prop["enum"] = p.enum_values
                if p.unit:
                    prop["unit"] = p.unit
                if p.label:
                    prop["title"] = p.label
            else:
                # Для конфигуратора: как заполнить форму
                prop["is_required"] = p.is_required
                if p.filter_type:
                    prop["filter_type"] = p.filter_type
                if p.data_source_type:
                    prop["data_source_type"] = p.data_source_type
                if p.options_config:
                    prop["options"] = p.options_config

            schema["properties"][p.param_name] = prop
            if p.is_required:
                schema["required"].append(p.param_name)
        return schema

    def get_options(self, context: str = 'user'):
        """
        Возвращает список опций для select'а.

        Стратегия выбирается по data_source_type.
        context: 'ai' или 'user' — влияет на стратегию (AI получает все опции).
        """
        model_class = self.product_model_class
        if not model_class:
            return []

        dst = self.data_source_type or 'global_model'
        cfg = self.options_config or {}

        try:
            if dst == 'foreign_key':
                field = model_class._meta.get_field(self.field_path or self.param_name)
                if hasattr(field, 'related_model') and field.related_model:
                    qs = field.related_model.objects.all()
                    if hasattr(field.related_model, 'is_active'):
                        qs = qs.filter(is_active=True)
                    if hasattr(field.related_model, 'sorting_order'):
                        qs = qs.order_by('sorting_order', 'name')
                    return [{"id": o.id, "name": str(o), "code": getattr(o, 'code', '') or ''} for o in qs[:500]]

            elif dst == 'field_values' or dst == 'unique_field_values':
                field_name = cfg.get('field', self.field_path or self.param_name)
                vals = model_class.objects.filter(is_active=True).values_list(field_name, flat=True).distinct()
                return [{"id": v, "name": str(v)} for v in vals if v is not None][:500]

            elif dst == 'global_model':
                model_ref = cfg.get('model', '')
                if model_ref:
                    from django.apps import apps
                    app_label, model_name = model_ref.split('.', 1)
                    opt_model = apps.get_model(app_label, model_name)
                    qs = opt_model.objects.all()
                    if cfg.get('active_only', True) and hasattr(opt_model, 'is_active'):
                        qs = qs.filter(is_active=True)
                    order_by = cfg.get('order_by', 'name')
                    if hasattr(opt_model, 'sorting_order'):
                        qs = qs.order_by('sorting_order', order_by)
                    else:
                        qs = qs.order_by(order_by)
                    return [{"id": o.id, "name": str(o), "code": getattr(o, 'code', '') or ''} for o in qs[:500]]

            elif dst == 'choices':
                field = model_class._meta.get_field(self.field_path or self.param_name)
                if hasattr(field, 'choices') and field.choices:
                    return [{"id": c[0], "name": str(c[1])} for c in field.choices]

            elif dst == 'custom':
                method_name = cfg.get('method', '')
                if method_name and hasattr(self, method_name):
                    return getattr(self, method_name)(context)

        except Exception:
            pass
        return []
