# price/models/ea_price_document.py
"""
EAPriceDocument — документ конфигуратора цен на электроприводы.

Документ задаёт контекст: тип цены, валюту, напряжение питания.
Строки документа — записи EAPriceConstructor, привязанные через FK document.

Workflow:
    1. Создать документ (черновик): указать name, price_variety, currency, power_supply
    2. Заполнить строки через интерфейс конфигуратора или Excel-импорт
    3. Провести → строки активируются (is_active=True)
    4. Отмена проведения → строки деактивируются
"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


class EAPriceDocument(models.Model):
    """
    Документ конфигуратора цен — заголовок.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        ON_APPROVAL = 'on_approval', _('На согласовании')
        POSTED = 'posted', _('Проведён')

    name = models.CharField(max_length=200, verbose_name=_("Название документа"))
    document_date = models.DateField(default=now, verbose_name=_("Дата документа"))
    description = models.TextField(blank=True, verbose_name=_("Комментарий"))

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
        verbose_name = _('Документ конфигуратора цен ЭП')
        verbose_name_plural = _('Документы конфигуратора цен ЭП')

    def __str__(self):
        labels = {'draft': '✎', 'on_approval': '⟳', 'posted': '✓'}
        label = labels.get(self.status, '?')
        return f"{label} {self.name} ({self.document_date})"

    @transaction.atomic
    def post(self):
        """Провести документ: активировать все строки."""
        if self.status == self.Status.POSTED:
            return

        from .ea_price_constructor import EAPriceConstructor
        EAPriceConstructor.objects.filter(document=self).update(is_active=True)

        self.status = self.Status.POSTED
        self.save(update_fields=['status'])

    @transaction.atomic
    def unpost(self):
        """Отменить проведение: деактивировать строки."""
        if self.status != self.Status.POSTED:
            return

        from .ea_price_constructor import EAPriceConstructor
        EAPriceConstructor.objects.filter(document=self).update(is_active=False)

        self.status = self.Status.DRAFT
        self.save(update_fields=['status'])
