# electric_actuators/models/ea_battery_option.py
"""Батарея положения безопасности ЭП.

Опция серии (through-модель уровня model_line): батарея (BAT), которая
питает привод при пропадании основного питания и обеспечивает положение
безопасности НЗ/НО (без батареи допустимо только «оставаться в текущем
положении» — Fail freeze). Участвует в артикуле (ext-позиция {bat}) и в
хэше конфигурации карточки каталога.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class ElectricBatteryOption(models.Model):
    """Опция батареи положения безопасности для серии электроприводов."""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='battery_options',
        verbose_name=_("Серия"),
        help_text=_("Серия электроприводов")
    )
    encoding = models.CharField(
        max_length=50, default='BAT',
        verbose_name=_("Кодировка"),
        help_text=_("Код опции для артикула (BAT)")
    )
    ext_encoding = models.CharField(
        max_length=10, blank=True, default='BAT',
        verbose_name=_("Ext-код"),
        help_text=_("Код позиции расширенного кода заказа")
    )
    name_i18n = models.JSONField(
        blank=True, default=dict,
        verbose_name=_("Переводы названия"),
        help_text=_("JSON: {\"ru\": ..., \"en\": ..., \"cn\": ...}")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение опции")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    is_default = models.BooleanField(default=False, verbose_name=_("Стандарт"))

    class Meta:
        verbose_name = _("Батарея положения безопасности ЭП")
        verbose_name_plural = _("Батареи положения безопасности ЭП")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.model_line} → BAT"
