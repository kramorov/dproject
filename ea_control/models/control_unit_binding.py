# ea_control/models/control_unit_binding.py
"""
Привязка блока управления (ControlUnit) к моделям электроприводов.

Структурная совместимость «какой БУ подходит к какой модели серии» —
отдельно от матрицы доступности по напряжению (slots.md §4.1/§5.6).

Решения (2026-11-12):

- привязка хранится **к конкретной модели** (ElectricActuatorModelLineItem),
  а не «к серии целиком»: nullable «вся серия» удобен в редакторе, но
  усложняет резолвер (null-ветка + дедуп). Кнопка «Вся серия» на фронте
  разворачивается в N строк по текущим моделям серии при сохранении;
- серия выводится из ``model_line_item.model_line`` — дублирующего поля
  ``model_line`` в таблице нет (меньше рассинхрона);
- напряжение в привязке не участвует — оно остаётся в матрице слота
  ``control_unit`` (CuMatrixEntry, координата power_supply);
- идентификация — по FK/pk (у ControlUnit к тому же есть стабильный ``key``);
  коды (``code``) для связей не используются.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class ControlUnitBinding(models.Model):
    """Пара «БУ ↔ модель ЭП» (структурная доступность без напряжения)."""

    control_unit = models.ForeignKey(
        'ControlUnit', on_delete=models.CASCADE, related_name='bindings',
        verbose_name=_("Блок управления"),
        help_text=_("Тип БУ, привязываемый к модели электропривода"),
    )
    model_line_item = models.ForeignKey(
        'electric_actuators.ElectricActuatorModelLineItem',
        on_delete=models.CASCADE, related_name='control_unit_bindings',
        verbose_name=_("Модель"),
        help_text=_("Модель в серии, к которой привязан БУ"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"))

    class Meta:
        verbose_name = _("Привязка БУ к модели")
        verbose_name_plural = _("Привязки БУ к моделям")
        ordering = ['sorting_order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['control_unit', 'model_line_item'],
                name='cu_binding_cu_item_unique'),
        ]

    def __str__(self):
        cu = self.control_unit.code if self.control_unit_id else '?'
        item = str(self.model_line_item) if self.model_line_item_id else '?'
        return f'{cu} → {item}'

    @property
    def model_line(self):
        """Серия, к которой относится модель (для группировки в UI/API)."""
        return self.model_line_item.model_line if self.model_line_item_id else None

    def clean(self):
        super().clean()
        if (self.model_line_item_id
                and self.model_line_item.model_line_id is None):
            raise ValidationError(
                {'model_line_item': _('Модель не привязана к серии.')})


def resolve_bound_units(model_line_item):
    """Привязки БУ к конкретной модели (горячий путь конфигуратора).

    Возвращает QuerySet[ControlUnitBinding] с ``control_unit`` (select_related)
    в порядке sorting_order привязки; нужные БУ — ``b.control_unit``.
    """
    return (ControlUnitBinding.objects
            .filter(model_line_item=model_line_item, is_active=True)
            .select_related('control_unit', 'control_unit__brand',
                            'control_unit__kind')
            .order_by('sorting_order', 'control_unit__code'))


def resolve_bound_unit_ids_for_series(model_line):
    """Все БУ, привязанные к любой модели серии (сводка) — без дублей."""
    return (ControlUnitBinding.objects
            .filter(model_line_item__model_line=model_line, is_active=True)
            .values_list('control_unit_id', flat=True).distinct())
