# filter_regulator/urls.py
from django.urls import path
from .views import (
    FilterRegulatorCatalogView,
    FilterRegulatorDetailView,
    FilterRegulatorFilterOptionsView,
    FilterRegulatorMetaView,
)
from .views.quickselect import FilterRegulatorQuickSelectView

urlpatterns = [
    path('quickselect/', FilterRegulatorQuickSelectView.as_view(), name='filter_regulator_quickselect'),
    path('catalog/', FilterRegulatorCatalogView.as_view(), name='filter_regulator_catalog'),
    path('catalog/<int:pk>/', FilterRegulatorDetailView.as_view(), name='filter_regulator_detail'),
    path('filters/', FilterRegulatorFilterOptionsView.as_view(), name='filter_regulator_filters'),
    path('meta/', FilterRegulatorMetaView.as_view(), name='filter_regulator_meta'),
]