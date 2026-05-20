# price/models/currency.py
"""
Валюта — справочник валют (RUB, USD, EUR, CNY...).

Используется:
    - PriceHistory — для фиксации цены в конкретной валюте
    - PriceDocumentItem — при создании документа цен
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import StructuredDataMixin


class Currency(StructuredDataMixin, models.Model):
    """
    Валюта (ISO 4217).

    Поля:
        name — название (Российский рубль)
        code — ISO-код (RUB, USD, EUR)
        symbol — знак (₽, $, €)
    """
    name = models.CharField(max_length=50, verbose_name=_("Название"),
                            help_text=_('Название валюты'))
    code = models.CharField(max_length=3, unique=True, verbose_name=_("Код"),
                            help_text=_("ISO 4217 код валюты (RUB, USD, EUR)"))
    symbol = models.CharField(max_length=10, blank=True, verbose_name=_('Символ'),
                              help_text=_('₽, $, €, ¥ и т.д.'))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание валюты'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Тип валюты')
        verbose_name_plural = _('Типы валюты')

    def __str__(self):
        return f"{self.name}"
