# documents/catalog/filter_defs.py
"""
Базовые FilterDefinition для журналов документов.

Стандартный набор фильтров, который можно переиспользовать
в любом журнале: статус, период, поиск.

Подклассы журналов могут добавлять свои fd_* для специфичных полей
(например, fd_price_variety для PriceDocumentJournal).
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType

# ── Статус ──

fd_status = FilterDefinition(
    param_name='status',
    model_field='status',
    filter_type=FilterType.CHOICE,
    data_source_type=DataSourceType.CHOICES,
    choices=[
        ('draft', 'Черновик'),
        ('on_approval', 'На согласовании'),
        ('posted', 'Проведён'),
        ('deleted', 'Удалён'),
    ],
    label='Статус',
    order=1,
)

# ── Период ──

fd_date_from = FilterDefinition(
    param_name='date_from',
    model_field='document_date',
    filter_type=FilterType.MIN,
    data_source_type=DataSourceType.CUSTOM,
    label='Дата от',
    order=2,
)

fd_date_to = FilterDefinition(
    param_name='date_to',
    model_field='document_date',
    filter_type=FilterType.MAX,
    data_source_type=DataSourceType.CUSTOM,
    label='Дата до',
    order=3,
)

# ── Поиск ──

fd_search = FilterDefinition(
    param_name='search',
    model_field='name',
    filter_type=FilterType.CONTAINS,
    data_source_type=DataSourceType.CUSTOM,
    label='Поиск',
    order=4,
)

# ── Стандартный набор для журнала ──

JOURNAL_FILTER_DEFINITIONS = [
    fd_status,
    fd_date_from,
    fd_date_to,
]
