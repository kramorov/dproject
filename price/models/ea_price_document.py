# price/models/ea_price_document.py
"""
EAPriceDocument — документ конфигуратора цен на электроприводы.

Наследует AbstractDocument из documents.

Документ задаёт контекст: тип цены, валюту, серию, напряжение питания.
Строки документа — записи EAPriceConstructor, привязанные через FK document.

Workflow:
    1. Создать документ (черновик): указать name, price_variety, currency,
       model_line, power_supply
    2. Заполнить строки через интерфейс конфигуратора или Excel-импорт
    3. Провести → строки активируются (is_active=True)
    4. Отмена проведения → строки деактивируются
"""
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from documents.models import AbstractDocument


class EAPriceDocument(AbstractDocument):
    """
    Документ конфигуратора цен — заголовок.

    Поля (общие — из AbstractDocument):
        name, code, description, status, document_date,
        created_at, updated_at, sorting_order, is_active

    Поля (специфичные):
        price_variety, currency, model_line, power_supply
    """

    NUMERATOR_PREFIX = 'EA-CONF'

    price_variety = models.ForeignKey(
        'price.PriceVariety', on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name=_('Тип цены'),
        help_text=_('Вид цены: РРЦ, опт, дилерская, ...')
    )

    currency = models.ForeignKey(
        'price.Currency', on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name=_('Валюта'),
        help_text=_('Валюта цены')
    )

    model_line = models.ForeignKey(
        'electric_actuators.ElectricActuatorModelLine',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='price_documents',
        verbose_name=_('Серия'),
        help_text=_('Серия электроприводов')
    )

    power_supply = models.ForeignKey(
        'electric_actuators.ElectricPowerSupplyOption',
        on_delete=models.PROTECT,
        related_name='price_documents',
        verbose_name=_('Напряжение питания'),
        help_text=_('Напряжение, для которого заполняются цены')
    )

    class Meta:
        verbose_name = _('Документ конфигуратора цен ЭП')
        verbose_name_plural = _('Документы конфигуратора цен ЭП')

    def get_items_related_name(self):
        return 'rows'

    @transaction.atomic
    def register_changes(self):
        """Провести документ: активировать все строки."""
        if self.status == self.Status.POSTED:
            return

        from .ea_price_constructor import EAPriceConstructor
        EAPriceConstructor.objects.filter(document=self).update(is_active=True)

        self.status = self.Status.POSTED
        self.save(update_fields=['status', 'updated_at'])

    @transaction.atomic
    def unregister_changes(self):
        """Отменить проведение: деактивировать строки."""
        if self.status != self.Status.POSTED:
            return

        from .ea_price_constructor import EAPriceConstructor
        EAPriceConstructor.objects.filter(document=self).update(is_active=False)

        self.status = self.Status.DRAFT
        self.save(update_fields=['status', 'updated_at'])

    # Совместимость со старым кодом
    post = register_changes
    unpost = unregister_changes
