# price/models/price_history.py
"""
PriceHistory — быстрый поиск актуальной цены товара.

Денормализованная таблица: один запрос → цена продукта.
Заполняется при активации PriceDocument (документ формирования цен).

Связь с товаром — через GenericForeignKey (ссылается на любую модель).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.models import StructuredDataMixin


class PriceHistory(StructuredDataMixin, models.Model):
    """
    Запись цены товара.

    Одна запись = один товар × один вид цены × одна валюта.
    is_current = True → актуальная цена (всегда одна на комбинацию).

    Поля:
        content_type + object_id — GFK на любую модель товара
        price_variety — вид цены (РРЦ, опт...)
        currency — валюта
        price — значение
        price_date — дата фиксации
        source_document — из какого PriceDocument (аудит)
        is_current — актуальная запись (True только у одной на товар+вид)
    """
    # GFK — ссылка на товар (любая модель)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        blank=True, null=True,  # null для обратной совместимости со старыми записями
        verbose_name=_("Тип товара"),
        help_text=_("Модель товара (PneumaticFitting, ElectricActuatorModelLineItem...)")
    )
    object_id = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_("ID товара")
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    # Денормализованные поля для обратной совместимости и быстрого поиска
    name = models.CharField(max_length=200, blank=True,
                            verbose_name=_("Название товара"),
                            help_text=_("Копируется из content_object при сохранении"))
    code = models.CharField(max_length=100, blank=True,
                            verbose_name=_("Код товара"),
                            help_text=_("Копируется из GFK-товара для быстрого поиска"))

    # Основная связь — через справочник номенклатуры
    sku = models.ForeignKey(
        'sku.SKU', on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='price_history',
        verbose_name=_("SKU"),
        help_text=_("Позиция номенклатуры (основной способ привязки)")
    )

    price_variety = models.ForeignKey(
        'price.PriceVariety', on_delete=models.PROTECT,
        verbose_name=_("Вид цены")
    )
    currency = models.ForeignKey(
        'price.Currency', on_delete=models.PROTECT,
        verbose_name=_("Валюта")
    )
    price = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name=_("Цена")
    )

    price_date = models.DateField(
        blank=True, null=True,
        verbose_name=_("Дата цены"),
        help_text=_("Дата, на которую зафиксирована цена")
    )

    # Аудит: из какого документа пришла цена
    source_document = models.ForeignKey(
        'price.PriceDocument', on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='history_records',
        verbose_name=_("Документ-источник"),
        help_text=_("PriceDocument, из которого взята цена")
    )

    # Только одна актуальная цена на товар+вид
    is_current = models.BooleanField(
        default=True,
        verbose_name=_("Актуальная"),
        help_text=_("Текущая действующая цена")
    )

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['-price_date']
        verbose_name = _('История цен')
        verbose_name_plural = _('История цен')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['price_variety', 'is_current']),
            models.Index(fields=['content_type', 'object_id', 'price_variety', 'is_current']),
            models.Index(fields=['sku']),
            models.Index(fields=['sku', 'price_variety', 'is_current']),
        ]

    def __str__(self):
        obj_name = str(self.content_object) if self.content_object else f"#{self.object_id}"
        return f"{obj_name} — {self.price_variety}: {self.price} {self.currency}"

    # ── SmartCatalogMixin compatibility (used when queried via UniversalAPIView) ──
    SELECT_RELATED_FIELDS = ['price_variety', 'currency']

    def get_compact_data(self):
        """Для UniversalAPIView — отдаёт полные данные."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'sku_id': self.sku_id,
            'sku_code': self.sku.code if self.sku else None,
            'sku_name': self.sku.name if self.sku else None,
            'price': float(self.price),
            'price_variety_id': self.price_variety_id,
            'price_variety_name': self.price_variety.name if self.price_variety else None,
            'currency_id': self.currency_id,
            'currency_name': self.currency.name if self.currency else None,
            'currency_symbol': self.currency.symbol if self.currency else None,
            'price_date': self.price_date.isoformat() if self.price_date else None,
            'is_current': self.is_current,
            'is_active': self.is_active,
            'object_id': self.object_id,
            'content_type_id': self.content_type_id,
        }

    def save(self, *args, **kwargs):
        """Авто-заполнение name и code из content_object."""
        if self.content_object and not self.name:
            self.name = str(self.content_object)[:200]
        if self.content_object and not self.code:
            self.code = getattr(self.content_object, 'code', '') or ''
        super().save(*args, **kwargs)

    @classmethod
    def get_current_price(cls, instance, price_variety):
        """
        Получить актуальную цену для товара и вида цены (через GFK).

        Args:
            instance — объект товара
            price_variety — экземпляр или id PriceVariety

        Returns:
            PriceHistory или None
        """
        ct = ContentType.objects.get_for_model(instance)
        return cls.objects.filter(
            content_type=ct,
            object_id=instance.pk,
            price_variety=price_variety,
            is_current=True,
            is_active=True,
        ).first()

    @classmethod
    def get_current_price_by_sku(cls, sku, price_variety):
        """
        Получить актуальную цену для позиции номенклатуры и вида цены.

        Args:
            sku — экземпляр SKU или sku_id
            price_variety — экземпляр или id PriceVariety

        Returns:
            PriceHistory или None
        """
        sku_id = sku.pk if hasattr(sku, 'pk') else sku
        return cls.objects.filter(
            sku_id=sku_id,
            price_variety=price_variety,
            is_current=True,
            is_active=True,
        ).first()
