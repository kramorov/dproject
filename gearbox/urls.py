# gearbox/urls.py
from django.urls import path
from gearbox.views.catalog import GearboxCatalogView, GearboxDetailView, GearboxFilterOptionsView
from gearbox.views.meta import GearboxMetaView

urlpatterns = [
    path('meta/', GearboxMetaView.as_view(), name='gearbox_meta'),
    path('catalog/', GearboxCatalogView.as_view(), name='gearbox_catalog'),
    path('catalog/<int:pk>/', GearboxDetailView.as_view(), name='gearbox_detail'),
    path('filters/', GearboxFilterOptionsView.as_view(), name='gearbox_filters'),
]
