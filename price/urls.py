# price/urls.py
from django.urls import path


from price.views.document_detail import PriceDocumentItemView , PriceDocumentDetailView
from price.views.document_journal import PriceDocumentListView
from price.views.price_catalog import PriceCatalogView
from price.views.price_filters import PriceFilterOptionsView

urlpatterns_admin = [
    path('', PriceCatalogView.as_view(), name='price_catalog'),
    path('filters/', PriceFilterOptionsView.as_view(), name='price_filter_options'),
    path('documents/', PriceDocumentListView.as_view(), name='price_document_list'),
    path('documents/<int:pk>/', PriceDocumentDetailView.as_view(), name='price_document_detail'),
    path('documents/<int:pk>/apply/', PriceDocumentDetailView.as_view(), name='price_document_apply'),
    path('documents/<int:doc_id>/items/', PriceDocumentItemView.as_view(), name='price_document_items'),
]

urlpatterns = urlpatterns_admin  # совместимость с include('price.urls')
