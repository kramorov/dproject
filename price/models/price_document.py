# price/models/price_document.py
"""
PriceDocument — документ формирования цен.

Группирует несколько ценовых позиций. При проведении — записывает
каждую позицию в PriceHistory как актуальную цену товара.

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
        status — draft / on_approval / posted
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        ON_APPROVAL = 'on_approval', _('На согласовании')
        POSTED = 'posted', _('Проведён')

    name = models.CharField(max_length=200, verbose_name=_("Название документа"))

    # Все строки документа — один тип товара
    item_content_type = models.ForeignKey(
        ContentType, on_delete=models.PROTECT,
        verbose_name=_("Тип товаров в документе"),
        help_text=_("Все позиции документа — одного типа (напр. PneumaticFitting)")
    )

    document_date = models.DateField(default=now, verbose_name=_("Дата документа"))
    description = models.TextField(blank=True, verbose_name=_("Комментарий"))

    # Значения по умолчанию для строк документа
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

    # ── Обратная совместимость ──
    @property
    def is_applied(self):
        """True если документ проведён (статус posted)."""
        return self.status == self.Status.POSTED

    @is_applied.setter
    def is_applied(self, value):
        """Сеттер для обратной совместимости (миграции, старый код)."""
        if value:
            self.status = self.Status.POSTED
        elif self.status == self.Status.POSTED:
            self.status = self.Status.DRAFT

    # ── SmartCatalogMixin compatibility ──
    SELECT_RELATED_FIELDS = ['item_content_type', 'default_price_variety', 'default_currency']

    def get_compact_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'document_date': self.document_date.isoformat() if self.document_date else None,
            'description': self.description,
            'status': self.status,
            'status_label': self.get_status_display(),
            'is_applied': self.is_applied,
            'item_content_type_id': self.item_content_type_id,
            'item_content_type_name': str(self.item_content_type) if self.item_content_type else None,
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
        """
        Применить цены из документа → записать в PriceHistory.

        Для каждой строки документа:
            - Помечает старую is_current=False
            - Создаёт новую PriceHistory с is_current=True

        После применения статус меняется на 'posted'.
        """
        if self.status == self.Status.POSTED:
            return  # Уже проведён
        if self.status == self.Status.ON_APPROVAL:
            pass  # Разрешено: на согласовании → проведён

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

        self.status = self.Status.POSTED
        self.save(update_fields=['status'])

    @transaction.atomic
    def unapply_prices(self):
        """
        Отмена проведения: удалить все записи PriceHistory,
        созданные этим документом, и вернуть статус в 'draft'.

        При отмене:
            - Удаляются записи PriceHistory с source_document=self
            - Для товаров, где были заменены чужие is_current, они НЕ восстанавливаются
              (архивная логика — нужно хранить предыдущие значения отдельно)
            - Статус документа → draft
        """
        if self.status != self.Status.POSTED:
            return  # Не проведён — нечего отменять

        # Собираем затронутые товары ДО удаления, чтобы понять, что делать с is_current
        affected = list(
            PriceHistory.objects
            .filter(source_document=self)
            .values('content_type_id', 'object_id', 'price_variety_id')
        )

        # Удаляем записи этого документа
        PriceHistory.objects.filter(source_document=self).delete()

        # Для каждого товара+вида: ищем последнюю по дате запись и помечаем is_current=True
        for row in affected:
            last = (
                PriceHistory.objects
                .filter(
                    content_type_id=row['content_type_id'],
                    object_id=row['object_id'],
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
