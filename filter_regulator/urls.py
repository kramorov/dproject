# filter_regulator/urls.py
from django.urls import path
from filter_regulator.catalog.views_list import FilterRegulatorCatalogView
from filter_regulator.catalog.views_detail import FilterRegulatorDetailView
from filter_regulator.catalog.views_filters import FilterRegulatorFilterOptionsView
from filter_regulator.catalog.views_engineer import FilterRegulatorEngineerView
from filter_regulator.catalog.views_engineer_filters import FilterRegulatorEngineerFilterOptionsView
from filter_regulator.views.meta import FilterRegulatorMetaView
from filter_regulator.views.quickselect import FilterRegulatorQuickSelectView

urlpatterns = [
    path('quickselect/', FilterRegulatorQuickSelectView.as_view(), name='filter_regulator_quickselect'),
    path('catalog/', FilterRegulatorCatalogView.as_view(), name='filter_regulator_catalog'),
    path('catalog/<int:pk>/', FilterRegulatorDetailView.as_view(), name='filter_regulator_detail'),
    path('filters/', FilterRegulatorFilterOptionsView.as_view(), name='filter_regulator_filters'),
    path('engineer/', FilterRegulatorEngineerView.as_view(), name='filter_regulator_engineer'),
    path('engineer/filters/', FilterRegulatorEngineerFilterOptionsView.as_view(), name='filter_regulator_engineer_filters'),
    path('meta/', FilterRegulatorMetaView.as_view(), name='filter_regulator_meta'),
]
