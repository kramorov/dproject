# gearbox/urls.py
from django.urls import path
from gearbox.views.catalog import GearboxCatalogView, GearboxDetailView, GearboxFilterOptionsView

urlpatterns = [
    path('catalog/', GearboxCatalogView.as_view(), name='gearbox_catalog'),
    path('catalog/<int:pk>/', GearboxDetailView.as_view(), name='gearbox_detail'),
    path('filters/', GearboxFilterOptionsView.as_view(), name='gearbox_filters'),
]
