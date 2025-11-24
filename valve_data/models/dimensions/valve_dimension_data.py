# valve_data/models/dimensions/valve_dimension_data.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from params.models import DnVariety, PnVariety
from valve_data.models.dimensions.dimension_table_parameter import DimensionTableParameter

import logging
logger = logging.getLogger(__name__)

class ValveDimensionData(models.Model):
    """Основная модель для хранения данных ВГХ:
    [PN][DN][параметр] - значение
    Список параметров - одинаковый для Dn и Pn
    привязывается к таблице ValveDimensionTable - где собственно и хранятся данные
    ValveDimensionData может быть несколько - по одной для разных Pn???
    Нет, пока храним все в одной таблице. При импорте данных из Excel синхронизируем по Dn и Pn
    Необходимо предусмотреть возможность удаления всех данных для некоторого Pn"""
    dn = models.ForeignKey(
        DnVariety,
        on_delete=models.CASCADE,
        related_name='dimension_data_dn',
        verbose_name=_('Dn')
    )
    pn = models.ForeignKey(
        PnVariety,
        on_delete=models.CASCADE,
        related_name='dimension_data_pn',
        verbose_name=_('Pn')
    )
    parameter = models.ForeignKey(
        DimensionTableParameter,
        on_delete=models.CASCADE,
        related_name='dimension_data',
        verbose_name=_('Параметр')
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Значение"),
        help_text=_('Числовое значение характеристики')
    )
    text_value = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Текстовое значение"),
        help_text=_('Текстовое значение (если не числовое)')
    )

    class Meta:
        verbose_name = _("Данные ВГХ")
        verbose_name_plural = _("Данные ВГХ")
        # unique_together = ['dn', 'pn', 'parameter'] # unique_together убрано - проверяем в коде
        ordering = ['pn__sorting_order', 'dn__sorting_order', 'parameter__sorting_order']
        indexes = [
            models.Index(fields=['pn', 'dn']),
            models.Index(fields=['parameter']),
        ]

    def __str__(self):
        value_display = self.value if self.value is not None else self.text_value
        return f"Pn{self.pn.name} Dn{self.dn.name} - {self.parameter.name}: {value_display}"

    def get_display_value(self):
        """Получить значение для отображения"""
        return self.text_value if self.value is None else self.value

