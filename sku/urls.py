# sku/urls.py
from django.urls import path
from .views import SkuListView, SkuBatchUpdateView

urlpatterns = [
    path('', SkuListView.as_view(), name='sku_list'),
    path('batch/', SkuBatchUpdateView.as_view(), name='sku_batch_update'),
]
