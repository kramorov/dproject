# price/models/price_document.py
"""
PriceDocument — документ формирования цен.

Наследует AbstractDocument из documents.

Группирует несколько ценовых позиций. При проведении — записывает
каждую позицию в PriceHistory как актуальную цену товара.

Все позиции привязаны к SKU (справочник номенклатуры).

Использование:
    1. Создать документ + строки (черновик)
    2. Перевести «На согласование» → блокировка
    3. «Провести» → для каждой строки создаётся/обновляется PriceHistory
    4. «Отмена проведения» → удаляются записи из PriceHistory, возврат в черновик
"""
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from documents.models import AbstractDocument, AbstractDocumentItem
from .price_history import PriceHistory


class PriceDocument(AbstractDocument):
    """
    Документ формирования цен — заголовок.

    Поля (общие — из AbstractDocument):
        name, code, description, status, document_date,
        created_at, updated_at, sorting_order, is_active

    Поля (специфичные):
        default_price_variety — тип цены по умолчанию для строк
        default_currency      — валюта по умолчанию для строк
    """

    NUMERATOR_PREFIX = 'ЦЕНА-'

    default_price_variety = models.ForeignKey(
        'price.PriceVariety', on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name=_("Тип цены"),
        help_text=_("Значение по умолчанию для новых строк")
    )
    default_currency = models.ForeignKey(
        'price.Currency', on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name=_("Валюта цены"),
        help_text=_("Значение по умолчанию для новых строк")
    )

    SELECT_RELATED_FIELDS = ['default_price_variety', 'default_currency']

    class Meta:
        verbose_name = _('Документ цен')
        verbose_name_plural = _('Документы цен')

    def get_compact_data(self):
        data = super().get_compact_data()
        data['default_price_variety_id'] = self.default_price_variety_id
        data['default_price_variety_name'] = (
            self.default_price_variety.name if self.default_price_variety else None
        )
        data['default_currency_id'] = self.default_currency_id
        data['default_currency_name'] = (
            self.default_currency.name if self.default_currency else None
        )
        data['default_currency_symbol'] = (
            self.default_currency.symbol if self.default_currency else None
        )
        data['items_count'] = self.items.filter(is_active=True).count()
        return data

    def get_items_related_name(self):
        return 'items'

    @transaction.atomic
    def register_changes(self):
        """Провести документ: записать цены в PriceHistory."""
        if self.status == self.Status.POSTED:
            return

        for item in self.items.filter(is_active=True).select_related('sku'):
            if not item.sku:
                continue

            PriceHistory.objects.filter(
                sku=item.sku,
                price_variety=item.price_variety,
                is_current=True,
            ).update(is_current=False)

            PriceHistory.objects.create(
                sku=item.sku,
                name=item.sku.name,
                code=item.sku.code,
                price_variety=item.price_variety,
                currency=item.currency,
                price=item.price,
                price_date=self.document_date,
                source_document=self,
                is_current=True,
            )

        self.status = self.Status.POSTED
        self.save(update_fields=['status', 'updated_at'])

    @transaction.atomic
    def unregister_changes(self):
        """Отменить проведение: удалить цены из PriceHistory."""
        if self.status != self.Status.POSTED:
            return

        affected = list(
            PriceHistory.objects
            .filter(source_document=self)
            .values('sku_id', 'price_variety_id')
        )

        PriceHistory.objects.filter(source_document=self).delete()

        for row in affected:
            last = (
                PriceHistory.objects
                .filter(
                    sku_id=row['sku_id'],
                    price_variety_id=row['price_variety_id'],
                    is_active=True,
                )
                .order_by('-price_date', '-id')
                .first()
            )
            if last and not last.is_current:
                last.is_current = True
                last.save(update_fields=['is_current'])

        self.status = self.Status.DRAFT
        self.save(update_fields=['status', 'updated_at'])

    # Совместимость со старым кодом
    apply_prices = register_changes
    unapply_prices = unregister_changes

    @property
    def is_applied(self):
        return self.is_posted


class PriceDocumentItem(AbstractDocumentItem):
    """
    Строка документа цен — одна позиция, привязанная к номенклатуре (SKU).

    Поля (общие — из AbstractDocumentItem):
        sorting_order, is_active, comment, created_at, updated_at

    Поля (специфичные):
        document, sku, price_variety, currency, price
    """
    document = models.ForeignKey(
        PriceDocument, on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Документ")
    )

    sku = models.ForeignKey(
        'sku.SKU', on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name=_("SKU"),
        help_text=_("Позиция номенклатуры")
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

    class Meta:
        verbose_name = _('Строка документа цен')
        verbose_name_plural = _('Строки документа цен')

    def __str__(self):
        return f"{self.sku.code if self.sku else '?'}: {self.price} {self.currency}"
