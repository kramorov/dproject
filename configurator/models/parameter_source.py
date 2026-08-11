"""
configurator/models/parameter_source.py

ParameterSource — справочник источников значений параметров.

Записи:
    user    — пользователь указывает явно в форме
    global  — из глобальных требований сборки
    parent  — от родительского компонента в дереве
    derived — вычисляется из выбранной модели через DerivationRule
"""
from django.db import models
from django.utils.translation import gettext_lazy as _lazy


class ParameterSource(models.Model):
    """Источник значения параметра для типа оборудования."""

    code = models.CharField(
        max_length=16, unique=True,
        verbose_name=_lazy("Код"),
        help_text=_lazy("Код источника: 'user', 'global', 'parent', 'derived'"),
    )
    name = models.CharField(
        max_length=64,
        verbose_name=_lazy("Название"),
        help_text=_lazy("Человекочитаемое название"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_lazy("Описание"),
        help_text=_lazy("Как работает этот источник"),
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "configurator_parameter_source"
        verbose_name = _lazy("Источник параметра")
        verbose_name_plural = _lazy("Источники параметров")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"

    @classmethod
    def seed_defaults(cls):
        """Создать 4 стандартных источника."""
        defaults = [
            ("user", "Пользователь", "Значение указывается пользователем в форме требований."),
            ("global", "Глобальные требования", "Значение берётся из глобальных требований сборки (температура, Exd, ...)."),
            ("parent", "Родительский компонент", "Значение наследуется от выбранного родительского компонента в дереве."),
            ("derived", "Каскад от модели", "Значение вычисляется из полей выбранной модели родителя через DerivationRule."),
        ]
        created = 0
        for code, name, desc in defaults:
            _, is_new = cls.objects.update_or_create(
                code=code,
                defaults={"name": name, "description": desc},
            )
            if is_new:
                created += 1
        return created
