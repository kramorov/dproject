# gearbox/urls.py
from django.urls import path
from gearbox.catalog.views_list import GearboxCatalogView
from gearbox.catalog.views_detail import GearboxDetailView
from gearbox.catalog.views_filters import GearboxFilterOptionsView
from gearbox.views.meta import GearboxMetaView
from gearbox.views.quickselect import GearboxQuickSelectView

urlpatterns = [
    path('quickselect/', GearboxQuickSelectView.as_view(), name='gearbox_quickselect'),
    path('meta/', GearboxMetaView.as_view(), name='gearbox_meta'),
    path('catalog/', GearboxCatalogView.as_view(), name='gearbox_catalog'),
    path('catalog/<int:pk>/', GearboxDetailView.as_view(), name='gearbox_detail'),
    path('filters/', GearboxFilterOptionsView.as_view(), name='gearbox_filters'),
]
