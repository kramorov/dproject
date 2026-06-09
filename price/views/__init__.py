# price/views/__init__.py
from .price_catalog import PriceCatalogView
from .price_filters import PriceFilterOptionsView
from .document_journal import PriceDocumentListView
from .document_detail import PriceDocumentDetailView
from .ea_configurator import EaPowerSuppliesView, EaConfiguratorOptionsView, EaConfiguratorDocumentView

__all__ = [
    'PriceCatalogView', 'PriceFilterOptionsView',
    'PriceDocumentListView', 'PriceDocumentDetailView',
    'EaPowerSuppliesView', 'EaConfiguratorOptionsView', 'EaConfiguratorDocumentView',
]
