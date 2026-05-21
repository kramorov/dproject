    # sku/models/sku.py
"""
SKU — справочник номенклатуры.

Единый реестр всех товаров/услуг, к которому привязываются:
- Модели оборудования (через SKUMixin)
- Цены (PriceHistory.sku)
- Документы цен (PriceDocumentItem)
- Счета, КП и прочие документы

Позволяет:
- Вести позиции без модели (просто код + описание)
- Унифицировать поиск и фильтрацию цен
- Упростить связи: один FK вместо GFK
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from producers.models import Brands


class SKU(models.Model):
    """
    Единица номенклатуры (Stock Keeping Unit).

    Поля:
        code            — уникальный код (артикул)
        name            — наименование
        equipment_type  — тип оборудования (FK → EquipmentType)
        brand           — бренд (FK → Producer), nullable
        source_ct/source_oid — GFK на модель-источник (если создан из модели)
        extra           — JSON с произвольными параметрами
    """
    name = models.TextField(
        verbose_name=_("Наименование"),
        help_text=_("Наименование товара/услуги")
    )
    code = models.CharField(
        max_length=100, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный артикул номенклатуры")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Описание номенклатурной позиции")
    )

    equipment_type = models.ForeignKey(
        'core.EquipmentType', on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name=_("Тип оборудования"),
        help_text=_("Классификатор типа оборудования")
    )
    brand = models.ForeignKey(
        Brands, on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_("Бренд"),
        help_text=_("Производитель / бренд")
    )

    # GFK — кто создал эту запись (модель оборудования)
    source_content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_("Тип модели-источника")
    )
    source_object_id = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_("ID модели-источника")
    )
    source_object = GenericForeignKey('source_content_type', 'source_object_id')

    extra = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Доп. параметры"),
        help_text=_("Произвольные поля в JSON")
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Создан"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлён"))

    class Meta:
        ordering = ['code']
        verbose_name = _('SKU')
        verbose_name_plural = _('SKU (Номенклатура)')
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['equipment_type']),
            models.Index(fields=['brand']),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

# ── SmartCatalogMixin compatibility ──
    SELECT_RELATED_FIELDS = ['equipment_type', 'brand']

    def get_compact_data(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'equipment_type_id': self.equipment_type_id,
            'equipment_type_name': self.equipment_type.name if self.equipment_type else None,
            'brand_id': self.brand_id,
            'brand_name': self.brand.name if self.brand else None,
            'is_active': self.is_active,
        }

