# sku/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SkuListView, SkuBatchUpdateView
from .api.views import SKUViewSet
from .api.search import SKUSearchView, SKUModelDetailView

router = DefaultRouter()
router.register(r'skus', SKUViewSet, basename='sku-crud')

urlpatterns = [
    path('', SkuListView.as_view(), name='sku_list'),
    path('batch/', SkuBatchUpdateView.as_view(), name='sku_batch_update'),
    path('search/', SKUSearchView.as_view(), name='sku_search'),
    path('model-detail/', SKUModelDetailView.as_view(), name='sku_model_detail'),
    path('', include(router.urls)),
]
