"""
ModelFieldSnapshot — снимок полей Django-модели, собранный интроспектором.

Назначение:
    Интроспектор (_introspect_model.py) «разматывает» модель оборудования через
    FK/OneToOne/M2M цепочки и собирает все reachable поля. Результат сохраняется
    в эту таблицу, чтобы не прогонять интроспекцию каждый раз.

    Снимок хранит:
    - field_path:    реальный путь к полю в Django-модели ('body__weight', 'work_temp_min')
    - param_name:    канонический ключ синхронизации ('temp_min', 'ip_id') — назначается
                     вручную/автоматически, объединяет разные модели к одному понятию
    - field_type:    тип Django-поля (fk, m2m, integer, boolean, ...)
    - target_model:  связанная модель для FK/M2M (app_label.ModelName)
    - depth:         уровень вложенности (0 = прямое поле, 1 = FK-цепочка)
    - filter_type:   инференция типа UI-фильтра (exact, choice, gte, boolean, ...)
    - data_source:   инференция источника данных (foreign_key, global_model, field_values, ...)
    - is_active:     включать ли в ETP (перенос через sync_to_etp)

    Поля-признаки неактивности (is_active=False) сохраняются, чтобы при добавлении
    новых полей в модель интроспектор мог показать diff — что появилось/исчезло.

Lifecycle:
    1. introspect(et_code) → создаёт/обновляет записи ModelFieldSnapshot
    2. Пользователь в админке/скрипте проставляет param_name и is_active
    3. sync_to_etp() → переносит активные поля в EquipmentTypeParameter
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class ModelFieldSnapshot(models.Model):
    """Снимок одного поля модели оборудования, собранный интроспектором."""

    FIELD_TYPE_CHOICES = [
        ("fk", _("Foreign Key")),
        ("m2m", _("Many-to-Many")),
        ("integer", _("Integer")),
        ("decimal", _("Decimal")),
        ("float", _("Float")),
        ("boolean", _("Boolean")),
        ("char", _("Char")),
        ("text", _("Text")),
        ("json", _("JSON")),
        ("other", _("Другой")),
    ]

    equipment_type = models.ForeignKey(
        "core.EquipmentType",
        on_delete=models.CASCADE,
        related_name="field_snapshots",
        verbose_name=_("Тип оборудования"),
        help_text=_("EquipmentType, для которого собран снимок"),
    )
    field_path = models.CharField(
        max_length=256,
        verbose_name=_("Путь к полю"),
        help_text=_("Реальный путь в Django-модели: 'work_temp_min', 'body__weight'"),
    )
    param_name = models.ForeignKey(
        "ParameterCatalog",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="field_snapshots",
        verbose_name=_("Канонический параметр"),
        help_text=_("Ссылка на запись в ParameterCatalog — унифицированное понятие для AI/UI. "
                    "Пусто = ещё не синхронизировано. На фронте — выпадающий список из каталога."),
    )
    field_type = models.CharField(
        max_length=16, choices=FIELD_TYPE_CHOICES, default="other",
        verbose_name=_("Тип поля"),
    )
    target_model = models.CharField(
        max_length=128, blank=True, null=True,
        verbose_name=_("Связанная модель"),
        help_text=_("app_label.ModelName для FK/M2M. Пусто для скалярных полей."),
    )
    source_model = models.CharField(
        max_length=128, blank=True, null=True,
        verbose_name=_("Модель-источник"),
        help_text=_("Где поле определено (для FK-цепочек может отличаться от equipment_type)"),
    )
    depth = models.IntegerField(
        default=0,
        verbose_name=_("Уровень вложенности"),
        help_text=_("0 = прямое поле модели, 1 = поле через один FK, 2 = через два"),
    )
    filter_type = models.CharField(
        max_length=32, blank=True, null=True,
        verbose_name=_("Тип фильтра"),
        help_text=_("Инференция: exact, choice, gte, boolean, icontains, ..."),
    )
    data_source_type = models.CharField(
        max_length=32, blank=True, null=True,
        verbose_name=_("Источник данных"),
        help_text=_("Инференция: foreign_key, global_model, field_values, choices"),
    )
    verbose_name = models.CharField(
        max_length=256, blank=True, null=True,
        verbose_name=_("Verbose name"),
        help_text=_("verbose_name из Django-поля (человекочитаемое название поля)"),
    )
    help_text = models.TextField(
        blank=True, null=True,
        verbose_name=_("Help text"),
        help_text=_("help_text из Django-поля (подсказка к назначению поля)"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Включать ли в ETP при sync_to_etp()"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Снимок поля модели")
        verbose_name_plural = _("Снимки полей моделей")
        ordering = ["equipment_type", "depth", "field_path"]
        unique_together = [("equipment_type", "field_path")]
        indexes = [
            models.Index(fields=["equipment_type", "is_active"]),
            models.Index(fields=["param_name"]),
        ]

    def __str__(self):
        return f"{self.equipment_type.code}.{self.field_path}"

    @property
    def is_synced(self) -> bool:
        """Поле уже привязано к каноническому param_name."""
        return bool(self.param_name)
