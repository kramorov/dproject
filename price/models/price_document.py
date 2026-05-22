# price/models/price_document.py
"""
PriceDocument — документ формирования цен.

Группирует несколько ценовых позиций. При проведении — записывает
каждую позицию в PriceHistory как актуальную цену товара.

Все позиции привязаны к SKU (справочник номенклатуры).

Статусы:
    draft       — Черновик (можно редактировать реквизиты и строки)
    on_approval — На согласовании (реквизиты и строки заблокированы)
    posted      — Проведён (цены записаны в PriceHistory)

Использование:
    1. Создать документ + строки (черновик)
    2. Перевести «На согласование» → блокировка
    3. «Провести» → для каждой строки создаётся/обновляется PriceHistory
    4. «Отмена проведения» → удаляются записи из PriceHistory, возврат в черновик
"""
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from core.models import StructuredDataMixin
from .price_history import PriceHistory


class PriceDocument(StructuredDataMixin, models.Model):
    """
    Документ формирования цен — заголовок.

    Поля:
        name — название документа
        document_date — дата документа
        description — комментарий
        status — draft / on_approval / posted
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        ON_APPROVAL = 'on_approval', _('На согласовании')
        POSTED = 'posted', _('Проведён')

    name = models.CharField(max_length=200, verbose_name=_("Название документа"))

    document_date = models.DateField(default=now, verbose_name=_("Дата документа"))
    description = models.TextField(blank=True, verbose_name=_("Комментарий"))

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

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Статус"),
        help_text=_("Черновик → На согласовании → Проведён")
    )

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['-document_date']
        verbose_name = _('Документ цен')
        verbose_name_plural = _('Документы цен')

    def __str__(self):
        labels = {'draft': '✎', 'on_approval': '⟳', 'posted': '✓'}
        label = labels.get(self.status, '?')
        return f"{label} {self.name} ({self.document_date})"

    @property
    def is_applied(self):
        return self.status == self.Status.POSTED

    @is_applied.setter
    def is_applied(self, value):
        if value:
            self.status = self.Status.POSTED
        elif self.status == self.Status.POSTED:
            self.status = self.Status.DRAFT

    SELECT_RELATED_FIELDS = ['default_price_variety', 'default_currency']

    def get_compact_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'document_date': self.document_date.isoformat() if self.document_date else None,
            'description': self.description,
            'status': self.status,
            'status_label': self.get_status_display(),
            'is_applied': self.is_applied,
            'default_price_variety_id': self.default_price_variety_id,
            'default_price_variety_name': self.default_price_variety.name if self.default_price_variety else None,
            'default_currency_id': self.default_currency_id,
            'default_currency_name': self.default_currency.name if self.default_currency else None,
            'default_currency_symbol': self.default_currency.symbol if self.default_currency else None,
            'items_count': self.items.filter(is_active=True).count(),
            'is_active': self.is_active,
        }

    @transaction.atomic
    def apply_prices(self):
        if self.status == self.Status.POSTED:
            return
        if self.status == self.Status.ON_APPROVAL:
            pass

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
        self.save(update_fields=['status'])

    @transaction.atomic
    def unapply_prices(self):
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
        self.save(update_fields=['status'])


class PriceDocumentItem(StructuredDataMixin, models.Model):
    """
    Строка документа цен — одна позиция, привязанная к номенклатуре (SKU).
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
    comment = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Примечание")
    )

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Строка документа цен')
        verbose_name_plural = _('Строки документа цен')

    def __str__(self):
        return f"{self.sku.code if self.sku else '?'}: {self.price} {self.currency}"
