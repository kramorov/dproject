# electric_actuators/models/ea_allowed_options.py
"""
Разрешённые опции на уровне серии (model_line).

Хранят encoding для пары (серия, опция) — единый источник истины
для всей серии, независимо от model_line_item и напряжения.

Через эти модели model_line_item выбирает доступные опции,
а encoding подставляется автоматически.

is_default остаётся в through-моделях уровня model_line_item
(ElectricSafetyPositionOption и т.д.).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class AllowedControlUnitOption(models.Model):
    """Блок управления, разрешённый для серии, с кодировкой."""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='allowed_control_units',
        verbose_name=_("Серия"),
        help_text=_("Серия электроприводов")
    )
    control_unit = models.ForeignKey(
        'params.ControlUnitInstalledOption',
        on_delete=models.CASCADE,
        related_name='allowed_in_model_lines',
        verbose_name=_("Блок управления"),
        help_text=_("Модель блока управления")
    )
    encoding = models.CharField(
        max_length=50,
        verbose_name=_("Кодировка"),
        help_text=_("Код опции для подстановки в артикул, например «L», «N», «M1»")
    )
    ext_encoding = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name=_("Ext-кодировка"),
        help_text=_("Код позиции расширенного кода заказа (ext); пусто — "
                    "фиксированный справочник CU_EXT в ea_ext_code")
    )
    power_supply = models.ForeignKey(
        'params.PowerSupplies',
        on_delete=models.PROTECT, null=True, blank=True,
        related_name='allowed_cu_power_supply_options',
        verbose_name=_("Напряжение питания мотора"),
        help_text=_("Напряжение, на котором доступен этот БУ (пусто — любое)")
    )
    model_line_item = models.ForeignKey(
        'ElectricActuatorModelLineItem',
        on_delete=models.CASCADE, null=True, blank=True,
        related_name='allowed_cu_options',
        verbose_name=_("Модель"),
        help_text=_("Перекрытие серийной пары для конкретной модели; "
                    "is_active=False — запрет пары (БУ×напряжение) для модели")
    )
    cu_power_supply = models.ForeignKey(
        'params.PowerSupplies',
        on_delete=models.PROTECT, null=True, blank=True,
        related_name='allowed_cu_power_supplies',
        verbose_name=_("Питание БУ"),
        help_text=_("Питание блока управления отдельно от питания привода; "
                    "пусто — от питания привода")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли в списках выбора")
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("По умолчанию"),
        help_text=_("Выбирать этот БУ по умолчанию при выборе напряжения")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки")
    )

    class Meta:
        verbose_name = _("Разрешённый БУ для серии")
        verbose_name_plural = _("Разрешённые БУ для серий")
        unique_together = ['model_line', 'control_unit', 'power_supply',
                           'model_line_item']
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.model_line} → {self.control_unit} ({self.encoding})"


def resolve_cu_pair(model_line, model_line_item, control_unit, power_supply):
    """Разрешение пары (модель, БУ, напряжение) для серии.

    Строки уровня модели (model_line_item=X) перекрывают серийные
    (model_line_item=None); конкретное напряжение перекрывает «любое»
    (power_supply=None). Строка с is_active=False — запрет: пара недоступна.

    Возвращает AllowedControlUnitOption или None (пара недоступна).
    """
    qs = AllowedControlUnitOption.objects.filter(
        model_line=model_line, control_unit=control_unit,
        power_supply__in=[power_supply, None])
    item_row = qs.filter(model_line_item=model_line_item).order_by(
        '-power_supply_id').first()
    if item_row is not None:
        return item_row if item_row.is_active else None
    series_row = qs.filter(model_line_item__isnull=True).order_by(
        '-power_supply_id').first()
    if series_row is not None:
        return series_row if series_row.is_active else None
    return None


class AllowedTurnCounterOption(models.Model):
    """Счётчик оборотов, разрешённый для серии, с кодировкой."""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='allowed_turn_counters',
        verbose_name=_("Серия"),
        help_text=_("Серия электроприводов")
    )
    turn_counter = models.ForeignKey(
        'params.TurnCounterOption',
        on_delete=models.CASCADE,
        related_name='allowed_in_model_lines',
        verbose_name=_("Счётчик оборотов")
    )
    encoding = models.CharField(
        max_length=50,
        verbose_name=_("Кодировка"),
        help_text=_("Код для подстановки в артикул")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))

    class Meta:
        verbose_name = _("Разрешённый счётчик для серии")
        verbose_name_plural = _("Разрешённые счётчики для серий")
        unique_together = ['model_line', 'turn_counter']
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.model_line} → {self.turn_counter} ({self.encoding})"

