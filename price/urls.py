# price/urls.py
from django.urls import path

from price.views.document_detail import (
    PriceDocumentItemView, PriceDocumentDetailView,
    PriceDocumentExportView, PriceDocumentImportView,
)
from price.views.document_journal import PriceDocumentListView
from price.views.price_catalog import PriceCatalogView
from price.views.price_filters import PriceFilterOptionsView
from price.views.price_snapshot import PriceSnapshotView
from price.views.ea_configurator import EaPowerSuppliesView, EaConfiguratorOptionsView, EaConfiguratorDocumentView

urlpatterns_admin = [
    path('', PriceCatalogView.as_view(), name='price_catalog'),
    path('filters/', PriceFilterOptionsView.as_view(), name='price_filter_options'),
    path('snapshot/', PriceSnapshotView.as_view(), name='price_snapshot'),

    # EA Price Configurator
    path('ea-configurator/power-supplies/', EaPowerSuppliesView.as_view(), name='ea_power_supplies'),
    path('ea-configurator/options/', EaConfiguratorOptionsView.as_view(), name='ea_configurator_options'),
    path('ea-configurator/documents/', EaConfiguratorDocumentView.as_view(), name='ea_configurator_docs'),
    path('ea-configurator/documents/<int:doc_id>/', EaConfiguratorDocumentView.as_view(), name='ea_configurator_doc_detail'),
    path('ea-configurator/create/', EaConfiguratorDocumentView.as_view(), name='ea_configurator_create'),
    path('ea-configurator/documents/<int:doc_id>/post/', EaConfiguratorDocumentView.as_view(), name='ea_configurator_post'),
    path('ea-configurator/documents/<int:doc_id>/unpost/', EaConfiguratorDocumentView.as_view(), name='ea_configurator_unpost'),

    # Documents
    path('documents/', PriceDocumentListView.as_view(), name='price_document_list'),
    path('documents/<int:pk>/', PriceDocumentDetailView.as_view(), name='price_document_detail'),
    path('documents/<int:pk>/apply/', PriceDocumentDetailView.as_view(), name='price_document_apply'),
    path('documents/<int:pk>/unapply/', PriceDocumentDetailView.as_view(), name='price_document_unapply'),
    path('documents/<int:doc_id>/items/', PriceDocumentItemView.as_view(), name='price_document_items'),
    path('documents/<int:pk>/export/', PriceDocumentExportView.as_view(), name='price_document_export'),
    path('documents/<int:pk>/import/', PriceDocumentImportView.as_view(), name='price_document_import'),
]

urlpatterns = urlpatterns_admin  # совместимость с include('price.urls')