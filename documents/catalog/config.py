# documents/catalog/config.py
"""
DocumentJournalConfig — конфигурация журнала документов.

Облегчённый аналог CatalogConfig, специфичный для журналов.
Использует те же FilterDefinition, но без split-логики
(exact/compatible для документов неактуально).

Совместим по контракту с фронтендом: возвращает {filters, show_compatible}.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type

from django.db.models import Model

from core.models.filter_definition import FilterDefinition


@dataclass
class DocumentJournalConfig:
    """
    Конфигурация журнала документов.

    Атрибуты:
        document_model      — класс модели документа
        filter_definitions  — список FilterDefinition для фильтрации
        select_related      — поля для select_related
        prefetch_fields     — поля для prefetch_related
        search_fields       — поля для полнотекстового поиска
        labels              — UI-метки (title, breadcrumbName, ...)

    Пример:
        PRICE_DOC_JOURNAL_CONFIG = DocumentJournalConfig(
            document_model=PriceDocument,
            filter_definitions=[
                fd_status,
                fd_date_from,
                fd_date_to,
                fd_price_variety,   # свой фильтр
                fd_search,
            ],
            select_related=['default_price_variety', 'default_currency'],
            prefetch_fields=['items'],
            search_fields=['name', 'description'],
            labels={
                'title': 'Документы цен',
                'breadcrumbName': 'Цены',
                'countLabel': 'Документов:',
                'searchPlaceholder': 'Поиск по документам...',
            },
        )
    """

    # ── Модель ──
    document_model: Type[Model]

    # ── Фильтры ──
    filter_definitions: List[FilterDefinition] = field(default_factory=list)

    # ── ORM-оптимизация ──
    select_related: List[str] = field(default_factory=list)
    prefetch_fields: List[str] = field(default_factory=list)
    search_fields: List[str] = field(default_factory=list)

    # ── UI ──
    labels: Dict[str, str] = field(default_factory=dict)

    # ── Методы ──

    def get_filter_options(self, queryset=None):
        """
        Вернуть опции всех фильтров в формате, совместимом с FilterSidebar.

        Returns:
            dict: {
                'filters': [{param_name, label, options, filter_type, ...}, ...],
                'show_compatible': False,
            }
        """
        filters = []
        for fd in self.filter_definitions:
            opts = fd.get_options(self.document_model, queryset=queryset)
            filters.append({
                'param_name': fd.param_name,
                'label': fd.label,
                'filter_type': fd.filter_type.value,
                'data_source_type': fd.data_source_type.value,
                'order': fd.order,
                'options': opts,
            })

        # Сортируем по order
        filters.sort(key=lambda f: f['order'])

        return {
            'filters': filters,
            'show_compatible': False,
        }
