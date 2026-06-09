# documents/models/abstract_document_item.py
"""
AbstractDocumentItem — абстрактная строка табличной части документа.

Общие поля: sorting_order, is_active, comment, created_at, updated_at.

Подклассы должны:
    - Добавить FK на документ (обычно с именем 'document')
    - Добавить содержательные поля (sku, price, quantity, ...)
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractDocumentItem(models.Model):
    """
    Абстрактная строка документа — табличная часть.

    Поля:
        sorting_order — порядок строки
        is_active     — активно (soft delete)
        comment       — примечание к строке
        created_at    — дата создания записи
        updated_at    — дата изменения записи
    """

    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_('Сортировка'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активно'),
    )
    comment = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Примечание'),
        help_text=_('Комментарий к строке документа'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создано'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Изменено'),
    )

    class Meta:
        abstract = True
        ordering = ['sorting_order']

    @classmethod
    def get_document_field_name(cls):
        """
        Имя FK-поля, связывающего строку с документом.

        По умолчанию 'document'. Переопределите, если FK называется иначе.
        """
        return 'document'

    def __str__(self):
        return f'Строка #{self.sorting_order}'
