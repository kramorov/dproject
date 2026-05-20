# price/models/price_variety.py
"""
Вид цены — справочник типов цен (РРЦ, опт, дилерская, партнёрская...).

Используется:
    - PriceHistory — к какому виду относится запись цены
    - PriceDocumentItem — какой вид цены устанавливается
    - PricingRule — к какому виду цены применяется правило
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import StructuredDataMixin


class PriceVariety(StructuredDataMixin, models.Model):
    """
    Вид цены.

    Примеры:
        РРЦ (рекомендованная розничная цена)
        Оптовая
        Дилерская
        Партнёрская (для сайтов партнёров)
        Закупочная (для внутреннего учёта)

    Поля:
        name — название вида
        code — краткий код
    """
    name = models.CharField(max_length=50, verbose_name=_("Название"),
                            help_text=_('Название вида цен'))
    code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код вида цен"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание вида цен'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Вид цены')
        verbose_name_plural = _('Виды цен')

    def __str__(self):
        return f"{self.name}"
