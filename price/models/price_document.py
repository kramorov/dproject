# price/models/price_document.py
"""
PriceDocument — документ формирования цен.

Группирует несколько ценовых позиций. При активации — записывает
каждую позицию в PriceHistory как актуальную цену товара.

Использование:
    1. Создать документ + строки (может быть черновиком)
    2. Кнопка «Применить» → для каждой строки создаётся/обновляется PriceHistory
    3. Старые записи PriceHistory помечаются is_current=False
"""
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from core.models import StructuredDataMixin
from .price_history import PriceHistory


class PriceDocument(StructuredDataMixin, models.Model):
    """
    Документ формирования цен — заголовок.

    Все строки документа относятся к одному типу товаров
    (item_content_type). Это упрощает таблицу и импорт из Excel.

    Поля:
        name — название документа
        item_content_type — тип товаров в строках
        document_date — дата документа
        description — комментарий
        is_applied — применён (цены записаны в PriceHistory)
    """
    name = models.CharField(max_length=200, verbose_name=_("Название документа"))

    # Все строки документа — один тип товара
    item_content_type = models.ForeignKey(
        ContentType, on_delete=models.PROTECT,
        verbose_name=_("Тип товаров в документе"),
        help_text=_("Все позиции документа — одного типа (напр. PneumaticFitting)")
    )

    document_date = models.DateField(default=now, verbose_name=_("Дата документа"))
    description = models.TextField(blank=True, verbose_name=_("Комментарий"))

    is_applied = models.BooleanField(
        default=False,
        verbose_name=_("Применён"),
        help_text=_("Цены из документа записаны в PriceHistory")
    )

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['-document_date']
        verbose_name = _('Документ цен')
        verbose_name_plural = _('Документы цен')

    def __str__(self):
        status = "✓" if self.is_applied else "✎"
        return f"{status} {self.name} ({self.document_date})"

    @transaction.atomic
    def apply_prices(self):
        """
        Применить цены из документа → записать в PriceHistory.

        Для каждой строки документа:
            - Помечает старую is_current=False
            - Создаёт новую PriceHistory с is_current=True
        """
        if self.is_applied:
            return  # Уже применён

        for item in self.items.filter(is_active=True):
            ct = item.content_type
            obj_id = item.object_id

            # Снимаем флаг is_current с предыдущих записей
            PriceHistory.objects.filter(
                content_type=ct,
                object_id=obj_id,
                price_variety=item.price_variety,
                is_current=True,
            ).update(is_current=False)

            # Создаём новую актуальную запись
            PriceHistory.objects.create(
                content_type=ct,
                object_id=obj_id,
                price_variety=item.price_variety,
                currency=item.currency,
                price=item.price,
                price_date=self.document_date,
                source_document=self,
                is_current=True,
            )

        self.is_applied = True
        self.save(update_fields=['is_applied'])


class PriceDocumentItem(StructuredDataMixin, models.Model):
    """
    Строка документа цен — одна позиция.

    Поля:
        document — FK на PriceDocument
        content_type + object_id — GFK на товар
        price_variety — вид цены
        currency — валюта
        price — значение
        comment — примечание к строке
    """
    document = models.ForeignKey(
        PriceDocument, on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Документ")
    )

    # GFK — ссылка на товар
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        verbose_name=_("Тип товара")
    )
    object_id = models.PositiveIntegerField(verbose_name=_("ID товара"))
    content_object = GenericForeignKey('content_type', 'object_id')

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
        obj_name = str(self.content_object) if self.content_object else f"#{self.object_id}"
        return f"{obj_name}: {self.price} {self.currency}"

    def get_object(self):
        """Получить объект товара через content_type родительского документа."""
        if self.document and self.document.item_content_type:
            try:
                return self.document.item_content_type.get_object_for_this_type(pk=self.object_id)
            except Exception:
                return None
        return None
